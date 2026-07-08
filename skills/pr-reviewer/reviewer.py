#!/usr/bin/env python3
"""
PR Reviewer — A CLI tool that fetches a GitHub PR diff, analyzes it for
security issues, bugs, style problems, and missing tests, then outputs
a structured Markdown review.

Usage:
    python reviewer.py --pr https://github.com/owner/repo/pull/123
    python reviewer.py --pr owner/repo#123
    python reviewer.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxx

Requires: requests (pip install requests)
GitHub token: set GITHUB_TOKEN env var, pass --token, or read from ~/.ghtoken
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' library required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


# ——— Configuration ———


GITHUB_API = "https://api.github.com"
USER_AGENT = "pr-reviewer-cli/1.0"


# ——— Helpers ———


def get_token(cli_token: Optional[str] = None) -> str:
    """Resolve GitHub token from CLI arg, env var, or file."""
    if cli_token:
        return cli_token
    env_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if env_token:
        return env_token
    token_file = Path.home() / ".ghtoken"
    if token_file.exists():
        return token_file.read_text().strip()
    print("Error: No GitHub token found. Set GITHUB_TOKEN or pass --token.", file=sys.stderr)
    sys.exit(1)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a PR URL or shorthand into (owner, repo, pr_number)."""
    # Full URL: https://github.com/owner/repo/pull/123
    m = re.match(
        r"(?:https?://github\.com/)?([\w.-]+)/([\w.-]+)/pull/(\d+)", url
    )
    if m:
        return m.group(1), m.group(2).rstrip("/"), int(m.group(3))
    # Shorthand: owner/repo#123
    m = re.match(r"([\w.-]+)/([\w.-]+)#(\d+)", url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    print(f"Error: Cannot parse PR URL: {url}", file=sys.stderr)
    sys.exit(1)


def github_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }


# ——— GitHub API ———


def fetch_pr(owner: str, repo: str, pr_number: int, token: str) -> dict:
    """Fetch PR metadata."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = requests.get(url, headers=github_headers(token), timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Fetch the unified diff for a PR."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = github_headers(token)
    headers["Accept"] = "application/vnd.github.v3.diff"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def fetch_files(owner: str, repo: str, pr_number: int, token: str) -> list:
    """Fetch the list of changed files."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    resp = requests.get(url, headers=github_headers(token), timeout=30)
    resp.raise_for_status()
    return resp.json()


# ——— Analysis ———


class Finding:
    severity: str   # "High", "Medium", "Low"
    category: str   # "Security", "Bug", "Style", "Test", "Performance", "General"
    file: str
    line: int
    message: str
    suggestion: str

    def __init__(self, severity, category, file, line, message, suggestion):
        self.severity = severity
        self.category = category
        self.file = file
        self.line = line
        self.message = message
        self.suggestion = suggestion


# Patterns that trigger findings with regex + heuristics
SECURITY_PATTERNS = [
    (r"\beval\s*\(", "Avoid eval() — arbitrary code execution risk"),
    (r"\bexec\s*\(", "Avoid exec() — arbitrary code execution risk"),
    (r"\bos\.system\s*\(", "Prefer subprocess.run() over os.system() — shell injection risk"),
    (r"\bsubprocess\.(call|Popen)\s*\([^)]*shell\s*=\s*True", "shell=True used — shell injection risk. Use list args instead"),
    (r"\bpickle\.(loads?|dump)", "pickle is unsafe for untrusted data — use json instead"),
    (r"(?i)password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
    (r"(?i)(api[_-]?key|secret|token)\s*=\s*['\"][^'\"]+['\"]", "Hardcoded credential detected"),
    (r"\braw_input\s*\(", "raw_input removed in Python 3; input() in Py2 is eval-equivalent"),
    (r"(?i)SELECT\s+.*\s+WHERE\s+.*[+=]\s*['\"]\s*\+", "Possible SQL injection — use parameterized queries"),
    (r"\bmd5\s*\(", "MD5 is cryptographically broken — use SHA-256"),
    (r"\bsha1\s*\(", "SHA-1 is cryptographically broken — use SHA-256"),
    (r"(?i)(?<![a-z])http://(?!(localhost|127\.0\.0\.1|0\.0\.0\.0))", "Use of http:// instead of https://"),
    (r"\byaml\.load\s*\(", "yaml.load() is unsafe — use yaml.safe_load()"),
    (r"\bassert\s+.*password", "Assert on passwords may be stripped in optimized mode (-O)"),
    (r"(?i)redirect\s*\(\s*request\s*\.", "Open redirect — validate redirect URLs against a whitelist"),
    (r"\.innerHTML\s*=", "innerHTML assignment — possible XSS. Use textContent or sanitize"),
    (r"\.dangerouslySetInnerHTML", "React dangerouslySetInnerHTML — possible XSS"),
    (r"document\.write\s*\(", "document.write() can introduce XSS — avoid"),
]

BUG_PATTERNS = [
    (r"except\s*:\s*$", "Bare except clause — catches SystemExit/KeyboardInterrupt too"),
    (r"except\s+Exception\s*:\s*\n\s*pass\b", "Silent exception pass — error swallowed without logging"),
    (r"if\s+(\w+)\s*=\s*[^=]", "Assignment in condition — likely meant '==' comparison"),
    (r"=\s*=\s*None\b", "Use 'is None' instead of '== None'"),
    (r"!=\s*None\b", "Use 'is not None' instead of '!= None'"),
    (r"\blen\(\w+\)\s*==\s*0", "Use 'not seq' instead of len(seq) == 0 (more Pythonic)"),
    (r"for\s+\w+\s+in\s+range\(len\(", "Use enumerate() instead of range(len(...))"),
    (r"\w+\.keys\(\)\s*\)\s*==\s*\[", "Comparing dict keys to list is fragile — use set operations"),
    (r"\breturn\s+None\b", "Bare 'return' is equivalent and more Pythonic than 'return None'"),
    (r"\.(read|write)\s*\([^)]*\)\s*$", "File opened without context manager — may leak handles"),
    (r"open\s*\([^)]*\)\s*\.(read|write)", "Use 'with open(...) as f:' instead of bare open"),
    (r"\bfloat\s*==\s*float", "Direct float equality comparison — use math.isclose()"),
    (r"\bdel\s+\w+\[\w+\]", "Repeated del on list elements in loop is O(n²)"),
    (r"\+\s*=?\s*1\s*$", "Use += 1 or prefer more descriptive increment pattern"),
    (r"if\s+\w+\s*==\s*True", "Redundant comparison to True — use 'if var:'"),
    (r"if\s+\w+\s*==\s*False", "Redundant comparison to False — use 'if not var:'"),
]

STYLE_PATTERNS = [
    (r"\t", "Tab character used — use spaces for indentation (PEP 8)"),
    (r"import\s+\w+\s*,\s*\w+", "Multiple imports on one line — split into separate import statements"),
    (r"^\s*#.*\S{101,}", "Line too long (>100 chars) — consider wrapping"),
    # Only flag trailing whitespace that's clearly intentional (has content before it)
    (r"\S\s{2,}$", "Trailing whitespace"),
    (r"def\s+\w+\s*\([^)]{101,}\)", "Function signature too long — split across multiple lines"),
    (r"^\s*from\s+\S+\s+import\s+\*", "Wildcard import — pollutes namespace. Import only what's needed"),
    (r"(?<!\w)print\s*\(.*\)(?!.*#.*(noqa|pragma))", "Debug print statement — remove before merge, or add # noqa comment"),
    (r"\bTODO\b", "TODO comment found — address before merging"),
    (r"\bFIXME\b", "FIXME comment found — address before merging"),
]


def analyze_diff(diff_text: str, files: list) -> list[Finding]:
    """Analyze a unified diff for issues and return structured findings."""
    findings = []

    # Build a map: filename -> list of (line_number, line_text) for added lines
    file_additions: dict[str, list[tuple[int, str]]] = {}
    current_file = None
    current_line_new = 0

    for line in diff_text.split("\n"):
        # Track file headers
        if line.startswith("diff --git"):
            m = re.search(r"diff --git a/(.+) b/(.+)", line)
            if m:
                current_file = m.group(2)
                file_additions.setdefault(current_file, [])
                current_line_new = 0
            continue
        if line.startswith("+++ "):
            continue
        if line.startswith("--- "):
            continue

        # Hunk header: @@ -old,count +new,count @@
        if line.startswith("@@"):
            m = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if m:
                current_line_new = int(m.group(1)) - 1
            continue

        if not current_file:
            continue

        if line.startswith("+"):
            current_line_new += 1
            file_additions.setdefault(current_file, []).append((current_line_new, line[1:]))
        elif line.startswith(" "):
            current_line_new += 1
        # Removals (-) don't advance line counter

    # Now scan additions for patterns
    for filename, additions in file_additions.items():
        for line_num, content in additions:
            # Security checks
            for pattern, message in SECURITY_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    findings.append(Finding(
                        severity="High",
                        category="Security",
                        file=filename,
                        line=line_num,
                        message=message,
                        suggestion=f"Review and refactor to remove the security concern on line {line_num}"
                    ))
                    break  # One finding per line per category

            # Bug checks
            for pattern, message in BUG_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    findings.append(Finding(
                        severity="Medium",
                        category="Bug",
                        file=filename,
                        line=line_num,
                        message=message,
                        suggestion=f"Fix the potential bug on line {line_num}"
                    ))
                    break

            # Style checks
            for pattern, message in STYLE_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    findings.append(Finding(
                        severity="Low",
                        category="Style",
                        file=filename,
                        line=line_num,
                        message=message,
                        suggestion=f"Address the style issue on line {line_num}"
                    ))
                    break

    # Check for missing tests
    test_files = [f for f in files if "test" in f.get("filename", "").lower()]
    src_files = [f for f in files if f.get("filename", "").endswith((".py", ".js", ".ts", ".go", ".rs", ".java", ".rb"))]
    if src_files and not test_files:
        findings.append(Finding(
            severity="Medium",
            category="Test",
            file="N/A",
            line=0,
            message="No test files included in this PR despite source code changes",
            suggestion="Add unit tests covering the new/modified functionality"
        ))

    # Check for large diffs (complexity heuristic)
    total_additions = sum(len(adds) for adds in file_additions.values())
    if total_additions > 500:
        findings.append(Finding(
            severity="Medium",
            category="General",
            file="N/A",
            line=0,
            message=f"Large PR: {total_additions}+ lines added across {len(file_additions)} files",
            suggestion="Consider splitting into smaller, focused PRs for easier review"
        ))

    return findings


def compute_confidence(findings: list[Finding]) -> str:
    """Compute a rough confidence score."""
    if not findings:
        return "High"
    high_count = sum(1 for f in findings if f.severity == "High")
    # More findings = lower confidence (more surface area to miss things)
    if high_count >= 3:
        return "Low"
    if high_count >= 1 or len(findings) >= 10:
        return "Medium"
    return "High"


def generate_summary(pr: dict, findings: list[Finding]) -> str:
    """Generate a 2-3 sentence summary of the changes."""
    title = pr.get("title", "Unknown")
    additions = pr.get("additions", "?")
    deletions = pr.get("deletions", "?")
    changed_files = pr.get("changed_files", "?")
    body = (pr.get("body") or "").strip()

    sentences = [
        f"This PR **\"{title}\"** modifies {changed_files} file(s) "
        f"(+{additions}/-{deletions} lines).",
    ]

    # Categorize findings
    high = [f for f in findings if f.severity == "High"]
    medium = [f for f in findings if f.severity == "Medium"]
    low = [f for f in findings if f.severity == "Low"]

    if high:
        sentences.append(f"⚠️ **{len(high)} high-severity** issue(s) found that require attention.")
    if medium:
        sentences.append(f"🟡 **{len(medium)} medium-severity** concern(s) identified.")
    if not findings:
        sentences.append("✅ No significant issues detected in automated analysis.")
    elif not high and len(findings) <= 3:
        sentences.append("Overall the PR looks manageable with minor improvements suggested.")

    if body:
        # Try to capture what the PR is about from the description
        first_line = body.split("\n")[0].strip()
        if len(first_line) < 120:
            sentences.insert(1, f"The described change: _{first_line}_")

    return " ".join(sentences)


# ——— Output Formatting ———


def format_markdown(pr: dict, findings: list[Finding], confidence: str, diff_url: str) -> str:
    """Produce the structured Markdown review."""
    summary = generate_summary(pr, findings)
    lines = []

    lines.append(f"## 🤖 Automated PR Review")
    lines.append(f"")
    lines.append(f"**PR:** [#{pr.get('number')}]({pr.get('html_url', '')}) — {pr.get('title', 'Unknown')}")
    lines.append(f"**Author:** @{pr.get('user', {}).get('login', 'unknown')}")
    lines.append(f"**Branch:** `{pr.get('head', {}).get('ref', '?')}` → `{pr.get('base', {}).get('ref', '?')}`")
    lines.append(f"")
    lines.append(f"### 📋 Summary")
    lines.append(summary)
    lines.append(f"")

    # Group findings by severity
    for sev_label, sev_emoji in [("High", "🔴"), ("Medium", "🟡"), ("Low", "🔵")]:
        group = [f for f in findings if f.severity == sev_label]
        if not group:
            continue
        lines.append(f"### {sev_emoji} {sev_label}-Severity Issues ({len(group)})")
        lines.append("")
        # Group within severity by category
        by_cat: dict[str, list] = {}
        for f in group:
            by_cat.setdefault(f.category, []).append(f)

        for cat, cat_findings in sorted(by_cat.items()):
            lines.append(f"#### {cat}")
            for f in cat_findings:
                file_ref = f"`{f.file}:{f.line}`" if f.line else f"`{f.file}`"
                lines.append(f"- **{file_ref}** — {f.message}")
                if f.suggestion:
                    lines.append(f"  > 💡 {f.suggestion}")
            lines.append("")

    lines.append(f"### 📊 Confidence Score: **{confidence}**")
    lines.append("")
    if confidence == "Low":
        lines.append("> ⚠️ Low confidence — this PR is large or has many findings. Manual review strongly recommended.")
    elif confidence == "Medium":
        lines.append("> 👀 Medium confidence — automated analysis found some concerns. Manual review recommended for high-severity items.")
    else:
        lines.append("> ✅ High confidence — automated analysis found few or no issues.")

    lines.append("")
    lines.append("---")
    lines.append(f"_Automated review by [pr-reviewer](https://github.com/chfr19820610-cell/claude-builders-bounty/tree/main/skills/pr-reviewer). Diff analyzed: [{pr.get('diff_url', diff_url)}]({diff_url})_")

    return "\n".join(lines)


# ——— CLI Entry Point ———


def main():
    parser = argparse.ArgumentParser(
        description="PR Reviewer — Analyze a GitHub PR and produce a structured review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reviewer.py --pr https://github.com/owner/repo/pull/123
  python reviewer.py --pr owner/repo#123 --token ghp_xxx
  python reviewer.py --pr https://github.com/owner/repo/pull/123 --comment  # post as PR review comment
        """.strip(),
    )
    parser.add_argument(
        "--pr", required=True,
        help="GitHub PR URL or owner/repo#NNN shorthand"
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--comment", action="store_true",
        help="Post the review as a PR comment (requires token with repo scope)"
    )
    args = parser.parse_args()

    token = get_token(args.token)
    owner, repo, pr_number = parse_pr_url(args.pr)

    print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    try:
        pr = fetch_pr(owner, repo, pr_number, token)
        diff_text = fetch_diff(owner, repo, pr_number, token)
        files = fetch_files(owner, repo, pr_number, token)
    except requests.HTTPError as e:
        print(f"Error fetching PR: {e}", file=sys.stderr)
        if e.response is not None:
            try:
                detail = e.response.json()
                print(f"  GitHub says: {detail.get('message', detail)}", file=sys.stderr)
            except Exception:
                pass
        sys.exit(1)

    print(f"📊 Analyzing {len(diff_text)} chars of diff across {len(files)} files...", file=sys.stderr)

    findings = analyze_diff(diff_text, files)
    confidence = compute_confidence(findings)

    review_md = format_markdown(pr, findings, confidence, pr.get("diff_url", ""))

    if args.comment:
        print("💬 Posting review comment...", file=sys.stderr)
        post_review_comment(owner, repo, pr_number, review_md, token)
        print("✅ Review posted!", file=sys.stderr)
    else:
        print(review_md)


def post_review_comment(owner: str, repo: str, pr_number: int, body: str, token: str):
    """Post the review as a comment on the PR."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{pr_number}/comments"
    resp = requests.post(
        url,
        headers=github_headers(token),
        json={"body": body},
        timeout=30,
    )
    resp.raise_for_status()
    comment_url = resp.json().get("html_url", "unknown")
    print(f"  Comment posted: {comment_url}", file=sys.stderr)


if __name__ == "__main__":
    main()
