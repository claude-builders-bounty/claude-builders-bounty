#!/usr/bin/env python3
"""
claude-review: Claude Code sub-agent that reviews a GitHub PR diff
and posts a structured Markdown comment.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
    claude-review --pr https://github.com/owner/repo/pull/123 --post-comment --inline
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# Data types
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    severity: str          # CRITICAL / HIGH / MEDIUM / LOW
    category: str          # Security, Error Handling, Performance, Style, Logic
    file: str
    line: Optional[int]
    description: str
    suggestion: str


@dataclass
class ReviewResult:
    pr_url: str
    pr_title: str
    pr_author: str
    summary: str
    risks: list[str]
    suggestions: list[str]
    findings: list[Finding]
    confidence: str        # High / Medium / Low
    files_changed: int
    lines_added: int
    lines_removed: int


# ──────────────────────────────────────────────────────────────────────────────
# GitHub API helpers
# ──────────────────────────────────────────────────────────────────────────────

def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse https://github.com/owner/repo/pull/123 -> (owner, repo, number)."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip())
    if not m:
        raise ValueError(f"Invalid PR URL: {url!r}. Expected https://github.com/owner/repo/pull/NNN")
    return m.group(1), m.group(2), int(m.group(3))


def github_request(path: str, accept: str = "application/vnd.github+json") -> dict | list | str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or _get_gh_token()
    url = f"https://api.github.com{path}" if path.startswith("/") else path
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "claude-review/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            if accept == "application/vnd.github.diff":
                return body
            return json.loads(body)
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API error {e.code}: {e.read().decode()[:400]}")


def github_request_post(url: str, data: bytes, method: str = "POST") -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or _get_gh_token()
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "claude-review/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API error {e.code} {method} {url}: {e.read().decode()[:200]}")


def _get_gh_token() -> str:
    """Try to pull a token from the gh CLI keychain."""
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    sys.exit(
        "No GitHub token found. Set GITHUB_TOKEN or log in with `gh auth login`."
    )


def fetch_pr_meta(owner: str, repo: str, number: int) -> dict:
    return github_request(f"/repos/{owner}/{repo}/pulls/{number}")


def fetch_pr_diff(owner: str, repo: str, number: int) -> str:
    return github_request(
        f"/repos/{owner}/{repo}/pulls/{number}",
        accept="application/vnd.github.diff",
    )


def fetch_pr_files(owner: str, repo: str, number: int) -> list:
    files = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files?per_page=100&page={page}"
        result = github_request(url)
        if not result:
            break
        files.extend(result)
        if len(result) < 100:
            break
        page += 1
    return files


def post_pr_comment(owner: str, repo: str, number: int, body: str) -> None:
    """Post or update a PR comment. Uses a marker to avoid duplicate comments."""
    marker = "<!-- pr-review-agent -->"
    marked_body = f"{marker}\n{body}"

    # Check for existing comment with our marker
    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    existing_comments = github_request(comments_url)
    existing_id = None
    if isinstance(existing_comments, list):
        for comment in existing_comments:
            if isinstance(comment.get("body"), str) and comment["body"].startswith(marker):
                existing_id = comment["id"]
                break

    if existing_id:
        # Update existing comment
        patch_url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{existing_id}"
        result = github_request_post(patch_url, json.dumps({"body": marked_body}).encode(), method="PATCH")
        print(f"✅ Comment updated: {result['html_url']}", file=sys.stderr)
    else:
        # Create new comment
        result = github_request_post(comments_url, json.dumps({"body": marked_body}).encode(), method="POST")
        print(f"✅ Comment posted: {result['html_url']}", file=sys.stderr)


def post_inline_review(owner: str, repo: str, pr_number: int, head_sha: str, findings: list, body: str) -> None:
    """Post an inline GitHub PR review with per-file comments where position data is available."""
    comments = []
    for f in findings:
        if f.file and f.line:
            comments.append({
                "path": f.file,
                "position": f.line,
                "body": f"**[{f.severity}] {f.category}**: {f.description}\n\n💡 {f.suggestion}",
            })

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    if comments:
        payload = {
            "commit_id": head_sha,
            "body": body,
            "event": "COMMENT",
            "comments": comments,
        }
    else:
        # Fallback: single review comment without inline positions
        payload = {
            "commit_id": head_sha,
            "body": body,
            "event": "COMMENT",
        }

    result = github_request_post(url, json.dumps(payload).encode(), method="POST")
    print(f"✅ Inline review posted: {result.get('html_url', '(no url)')}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# Static analysis patterns
# ──────────────────────────────────────────────────────────────────────────────

SECURITY_PATTERNS = [
    # (regex, description, suggestion)
    (r'(?i)(password|passwd|secret|api_key|apikey|token)\s*=\s*["\'][^"\']{4,}["\']',
     "Possible hardcoded credential",
     "Move secrets to environment variables or a secrets manager"),
    (r'(?i)eval\s*\(',
     "Use of eval() — arbitrary code execution risk",
     "Avoid eval(); use safer alternatives like ast.literal_eval() or JSON parsing"),
    (r'(?i)subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True',
     "shell=True in subprocess — command injection risk",
     "Pass a list of arguments instead of a shell string"),
    (r'(?i)pickle\.(load|loads)\s*\(',
     "Unpickling untrusted data can execute arbitrary code",
     "Use JSON or another safe serialisation format for untrusted input"),
    (r'(?i)SELECT\s+\*?\s+FROM\s+\w+\s+WHERE\s+\w+\s*=\s*["\']?\s*\+',
     "Possible SQL injection via string concatenation",
     "Use parameterised queries / prepared statements"),
    (r'(?i)\.innerHTML\s*=',
     "Direct innerHTML assignment — XSS risk",
     "Use textContent or sanitise input with DOMPurify"),
    (r'(?i)md5\s*\(',
     "MD5 is cryptographically broken",
     "Use SHA-256 or bcrypt for security-sensitive hashing"),
    (r'(?i)verify\s*=\s*False',
     "SSL certificate verification disabled",
     "Remove verify=False; fix the certificate instead"),
]

ERROR_HANDLING_PATTERNS = [
    (r'except\s*:',
     "Bare except clause swallows all exceptions including KeyboardInterrupt",
     "Catch specific exception types, e.g. `except ValueError:`"),
    (r'except\s+Exception\s*:\s*\n\s*pass',
     "Silently ignoring exceptions hides bugs",
     "At minimum log the exception with logging.exception()"),
    (r'\.catch\s*\(\s*\(\s*\)\s*=>',
     "Empty .catch() silently swallows Promise rejections",
     "Log or re-raise in .catch() handlers"),
]

QUALITY_PATTERNS = [
    (r'(?m)#\s*TODO|#\s*FIXME|//\s*TODO|//\s*FIXME',
     "TODO/FIXME marker in diff",
     "Resolve or create a tracked issue for this before merging"),
    (r'console\.log\s*\(',
     "console.log left in production code",
     "Remove debug logs or replace with a proper logger"),
    (r'(?m)^\+.{200,}',
     "Very long line (>200 chars) added",
     "Break long lines to improve readability"),
]

ALL_PATTERN_GROUPS = [
    ("Security",        "CRITICAL", SECURITY_PATTERNS),
    ("Error Handling",  "HIGH",     ERROR_HANDLING_PATTERNS),
    ("Code Quality",    "MEDIUM",   QUALITY_PATTERNS),
]


# ──────────────────────────────────────────────────────────────────────────────
# Diff analysis
# ──────────────────────────────────────────────────────────────────────────────

def analyse_diff(diff: str) -> list[Finding]:
    """Run static pattern matching over added lines in the diff."""
    findings: list[Finding] = []
    current_file = "unknown"
    current_line = 0

    for raw_line in diff.splitlines():
        if raw_line.startswith("diff --git"):
            m = re.search(r" b/(.+)$", raw_line)
            current_file = m.group(1) if m else "unknown"
            current_line = 0
        elif raw_line.startswith("@@"):
            m = re.search(r"\+(\d+)", raw_line)
            current_line = int(m.group(1)) - 1 if m else current_line
        elif raw_line.startswith("+") and not raw_line.startswith("+++"):
            current_line += 1
            added = raw_line[1:]  # strip leading '+'
            for category, severity, patterns in ALL_PATTERN_GROUPS:
                for pattern, description, suggestion in patterns:
                    if re.search(pattern, added):
                        findings.append(Finding(
                            severity=severity,
                            category=category,
                            file=current_file,
                            line=current_line,
                            description=description,
                            suggestion=suggestion,
                        ))
        elif raw_line.startswith(" ") or raw_line.startswith("-"):
            if not raw_line.startswith("---"):
                current_line += 1

    return findings


def compute_confidence(meta: dict, findings: list[Finding]) -> str:
    """Confidence in the review: High = small diff + no critical, Low = huge diff."""
    additions = meta.get("additions", 0)
    deletions = meta.get("deletions", 0)
    total = additions + deletions
    critical = sum(1 for f in findings if f.severity == "CRITICAL")

    if total > 2000 or critical >= 3:
        return "Low"
    if total > 500 or critical >= 1:
        return "Medium"
    return "High"


def build_summary(meta: dict, files: list, findings: list[Finding]) -> tuple[str, list[str], list[str]]:
    """Build the three narrative sections."""
    n_files = meta.get("changed_files", len(files))
    adds = meta.get("additions", 0)
    dels = meta.get("deletions", 0)
    critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
    high_count = sum(1 for f in findings if f.severity == "HIGH")

    # Summary sentence
    file_names = ", ".join(f['filename'] for f in files[:3])
    extra = f" and {n_files - 3} more" if n_files > 3 else ""
    severity_note = ""
    if critical_count:
        severity_note = f" The review flagged {critical_count} critical security issue(s) that should be resolved before merge."
    elif high_count:
        severity_note = f" {high_count} high-severity error-handling issue(s) were found."

    summary = (
        f"This PR modifies {n_files} file(s) ({file_names}{extra}), "
        f"adding {adds} and removing {dels} lines.{severity_note}"
    )

    # Risks
    risks: list[str] = []
    seen: set[str] = set()
    for f in findings:
        if f.severity in ("CRITICAL", "HIGH"):
            key = f"{f.category}:{f.description[:60]}"
            if key not in seen:
                seen.add(key)
                risks.append(f"**[{f.severity}]** `{f.file}:{f.line}` — {f.description}")
    if not risks:
        risks.append("No critical or high-severity risks detected.")

    # Suggestions
    suggestions: list[str] = []
    seen2: set[str] = set()
    for f in findings:
        key = f.suggestion[:80]
        if key not in seen2:
            seen2.add(key)
            suggestions.append(f.suggestion)
    # Generic best-practice suggestions when diff is large
    if meta.get("additions", 0) > 300 and "Consider adding unit tests" not in suggestions:
        suggestions.append("Consider adding unit tests for the new logic to prevent regressions.")
    if not suggestions:
        suggestions.append("No improvement suggestions — looks clean!")

    return summary, risks, suggestions


# ──────────────────────────────────────────────────────────────────────────────
# Claude API / CLI integration (optional — falls back to static analysis)
# ──────────────────────────────────────────────────────────────────────────────

def call_claude_api(diff: str, meta: dict) -> Optional[dict]:
    """
    If ANTHROPIC_API_KEY is set, ask Claude API to produce a structured JSON review.
    Returns None on any failure so the caller can fall back gracefully.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    # Truncate diff to ~8 000 tokens worth of text to stay within context limits
    truncated = diff[:24_000]
    if len(diff) > 24_000:
        truncated += "\n\n[... diff truncated for brevity ...]"

    prompt = f"""You are a senior software engineer reviewing a GitHub pull request.

PR title: {meta.get('title', 'unknown')}
Author: {meta.get('user', {}).get('login', 'unknown')}

Diff:
{truncated}

Respond with ONLY a JSON object matching this schema (no markdown fences):
{{
  "summary": "2-3 sentence summary of the changes",
  "risks": ["risk 1", "risk 2"],
  "suggestions": ["suggestion 1", "suggestion 2"],
  "confidence": "High|Medium|Low"
}}
"""

    payload = json.dumps({
        "model": "claude-opus-4-5",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            text = data["content"][0]["text"]
            return json.loads(text)
    except Exception as exc:
        print(f"⚠️  Claude API call failed ({exc}); using static analysis only.", file=sys.stderr)
        return None


def call_claude_code_cli(diff_content: str, pr_url: str) -> Optional[dict]:
    """
    Try to use the Claude Code CLI ('claude' command) for the review.
    Falls back to call_claude_api() if the CLI is not available.
    Returns a dict with review data, or None on failure.
    """
    prompt = f"Review this PR diff for issues:\n\n{diff_content[:8000]}"
    try:
        result = subprocess.run(
            ["claude", "--print", prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Try to parse structured JSON from the output
            text = result.stdout.strip()
            # Look for a JSON block in the output
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            # Return as a plain summary if not JSON
            return {"summary": text[:1000], "risks": [], "suggestions": [], "confidence": "Medium"}
    except FileNotFoundError:
        print("ℹ️  Claude CLI not found; falling back to API.", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("⚠️  Claude CLI timed out; falling back to API.", file=sys.stderr)
    except Exception as exc:
        print(f"⚠️  Claude CLI error ({exc}); falling back to API.", file=sys.stderr)

    # Fallback: use the API (needs meta, but we only have diff here — pass minimal meta)
    return None


def call_claude(diff: str, meta: dict) -> Optional[dict]:
    """
    Try Claude Code CLI first, then fall back to direct API call.
    Returns None on all failures so callers can use static analysis only.
    """
    cli_result = call_claude_code_cli(diff, meta.get("html_url", ""))
    if cli_result is not None:
        print("✨ Claude CLI enrichment applied.", file=sys.stderr)
        return cli_result
    return call_claude_api(diff, meta)


# ──────────────────────────────────────────────────────────────────────────────
# Markdown renderer
# ──────────────────────────────────────────────────────────────────────────────

SEVERITY_EMOJI = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}
CONFIDENCE_EMOJI = {"High": "✅", "Medium": "⚠️", "Low": "❌"}


def render_markdown(result: ReviewResult) -> str:
    lines = [
        "## 🤖 Claude Code Review",
        "",
        f"> **PR**: [{result.pr_title}]({result.pr_url})  ",
        f"> **Author**: @{result.pr_author}  ",
        f"> **Changes**: +{result.lines_added} / -{result.lines_removed} across {result.files_changed} file(s)",
        "",
        "---",
        "",
        "### 📋 Summary",
        "",
        result.summary,
        "",
        "### ⚠️ Identified Risks",
        "",
    ]
    for risk in result.risks:
        lines.append(f"- {risk}")

    lines += ["", "### 💡 Improvement Suggestions", ""]
    for sug in result.suggestions:
        lines.append(f"- {sug}")

    if result.findings:
        lines += ["", "### 🔍 Detailed Findings", ""]
        for f in result.findings:
            emoji = SEVERITY_EMOJI.get(f.severity, "•")
            loc = f"`{f.file}:{f.line}`" if f.line else f"`{f.file}`"
            lines.append(f"| {emoji} {f.severity} | **{f.category}** | {loc} | {f.description} |")
            if lines[-3] != "| Severity | Category | Location | Description |":
                # insert header if needed
                pass
        # Add a proper table header before findings rows
        table_start = next(i for i, l in enumerate(lines) if l.startswith("| 🔴") or l.startswith("| 🟠") or l.startswith("| 🟡") or l.startswith("| 🔵"))
        lines.insert(table_start, "| Severity | Category | Location | Description |")
        lines.insert(table_start + 1, "|----------|----------|----------|-------------|")

    conf_emoji = CONFIDENCE_EMOJI.get(result.confidence, "")
    lines += [
        "",
        f"### {conf_emoji} Confidence: **{result.confidence}**",
        "",
        "_Confidence reflects diff size and the density of findings. "
        "A High-confidence review means the diff is focused and no blockers were found._",
        "",
        "---",
        "_Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty/tree/main/agents/pr-review)_",
    ]
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────────────────────────────────────

def review_pr(pr_url: str) -> tuple[ReviewResult, str]:
    owner, repo, number = parse_pr_url(pr_url)
    print(f"🔍 Fetching PR #{number} from {owner}/{repo}…", file=sys.stderr)

    meta = fetch_pr_meta(owner, repo, number)
    diff = fetch_pr_diff(owner, repo, number)
    files = fetch_pr_files(owner, repo, number)

    print(f"📂 {meta['changed_files']} file(s), +{meta['additions']} -{meta['deletions']}", file=sys.stderr)

    # Static analysis
    findings = analyse_diff(diff)
    summary, risks, suggestions = build_summary(meta, files, findings)
    confidence = compute_confidence(meta, findings)

    # Optional: augment with Claude (CLI first, then API)
    claude_result = call_claude(diff, meta)
    if claude_result:
        summary = claude_result.get("summary", summary)
        if claude_result.get("risks"):
            risks = claude_result["risks"]
        if claude_result.get("suggestions"):
            suggestions = claude_result["suggestions"]
        confidence = claude_result.get("confidence", confidence)

    result = ReviewResult(
        pr_url=pr_url,
        pr_title=meta.get("title", f"PR #{number}"),
        pr_author=meta.get("user", {}).get("login", "unknown"),
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        findings=findings,
        confidence=confidence,
        files_changed=meta.get("changed_files", len(files)),
        lines_added=meta.get("additions", 0),
        lines_removed=meta.get("deletions", 0),
    )
    markdown = render_markdown(result)
    return result, markdown


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — structured Markdown review from a PR URL",
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--post-comment", action="store_true", help="Post the review as a GitHub PR comment")
    parser.add_argument("--inline", action="store_true", help="Post inline review comments on the PR diff (requires --post-comment)")
    parser.add_argument("--output", metavar="FILE", help="Write Markdown review to FILE instead of stdout")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of Markdown")
    args = parser.parse_args()

    result, markdown = review_pr(args.pr)

    if args.json:
        import dataclasses
        out = json.dumps(dataclasses.asdict(result), indent=2)
        print(out)
    elif args.output:
        with open(args.output, "w") as fh:
            fh.write(markdown)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(markdown)

    if args.post_comment:
        owner, repo, number = parse_pr_url(args.pr)
        if args.inline:
            meta = result  # head sha needed
            # Fetch meta again for head SHA
            import urllib.parse
            raw_meta = fetch_pr_meta(owner, repo, number)
            head_sha = raw_meta.get("head", {}).get("sha", "")
            post_inline_review(owner, repo, number, head_sha, result.findings, markdown)
        else:
            post_pr_comment(owner, repo, number, markdown)


if __name__ == "__main__":
    main()
