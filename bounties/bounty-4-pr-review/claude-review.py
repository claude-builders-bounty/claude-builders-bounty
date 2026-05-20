#!/usr/bin/env python3
"""Claude Code PR Review Agent — Analyzes GitHub PR diffs programmatically."""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path


# ── Helpers ──────────────────────────────────────────────────────────────────


def die(msg: str):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_github_token() -> str:
    """Return a GitHub token from GITHUB_TOKEN env var, or ~/.config/gh/hosts.yml."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token

    # Try the token file used by this environment
    token_file = Path("/tmp/gh_token.json")
    if token_file.exists():
        try:
            with open(token_file) as f:
                data = json.load(f)
            tok = data.get("access_token") or data.get("token")
            if tok:
                return tok
        except (json.JSONDecodeError, KeyError, OSError):
            pass

    # Fallback: ~/.config/gh/hosts.yml
    gh_config = Path.home() / ".config" / "gh" / "hosts.yml"
    if gh_config.exists():
        try:
            text = gh_config.read_text()
            m = re.search(r"(?:github\.com|github\.com[\s\S]*?oauth_token:\s*['\"]?)(\S+)['\"]?", text)
            if m:
                return m.group(1).strip().strip("'\"")
        except OSError:
            pass

    die(
        "No GitHub token found. Set GITHUB_TOKEN env var, ensure ~/.config/gh/hosts.yml "
        "has one, or place a JSON token in /tmp/gh_token.json"
    )


def fetch(url: str, token: str) -> str:
    """GET |url| and return the response body.  Raises on HTTP errors."""
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "claude-review-agent/1.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        die(f"GitHub API error {exc.code} for {url}\n{body[:500]}")
    except urllib.error.URLError as exc:
        die(f"Network error: {exc.reason}")


def parse_pr_url(url: str):
    """Extract owner, repo, pr_number from a GitHub PR URL."""
    m = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)",
        url,
    )
    if not m:
        die(f"Invalid PR URL: {url!r}\nExpected: https://github.com/owner/repo/pull/123")
    return m.group(1), m.group(2), int(m.group(3))


# ── Diff parsing ─────────────────────────────────────────────────────────────


def parse_diff(diff_text: str):
    """Parse a unified diff into a list of per-file results.

    Each result is a dict:
        path: str
        added: int
        removed: int
        lines: list[str]   (the full per-file diff lines, including headers)
    """
    files = []
    current = None

    for line in diff_text.splitlines(keepends=True):
        # diff --git a/... b/...
        if line.startswith("diff --git "):
            if current is not None:
                files.append(current)
            # pick the "b/" path
            parts = line.split()
            path = parts[-1].removeprefix("b/") if len(parts) >= 3 else "unknown"
            current = {"path": path, "added": 0, "removed": 0, "lines": [line]}
        elif line.startswith("--- a/"):
            if current is None:
                current = {"path": "unknown", "added": 0, "removed": 0, "lines": []}
            current["lines"].append(line)
        elif line.startswith("+++ b/"):
            if current is None:
                current = {"path": "unknown", "added": 0, "removed": 0, "lines": []}
            current["lines"].append(line)
        elif line.startswith("@@ "):
            if current is not None:
                current["lines"].append(line)
        elif current is not None:
            current["lines"].append(line)
            if line.startswith("+"):
                current["added"] += 1
            elif line.startswith("-"):
                current["removed"] += 1

    if current is not None:
        files.append(current)
    return files


# ── Analysis ─────────────────────────────────────────────────────────────────


def count_file_types(files):
    """Return a dict mapping extension -> count."""
    ext_counts: dict[str, int] = defaultdict(int)
    for f in files:
        p = Path(f["path"])
        ext = p.suffix if p.suffix else "(none)"
        ext_counts[ext] += 1
    return dict(ext_counts)


def total_changes(files):
    added = sum(f["added"] for f in files)
    removed = sum(f["removed"] for f in files)
    return added, removed


def analyze_risks(files):
    """Return a list of (risk_title, details) tuples."""
    risks = []
    total_added, total_removed = total_changes(files)
    total_lines = total_added + total_removed

    # 1. Large PR
    if total_lines > 500:
        risks.append(
            (
                "Large PR size",
                f"This PR touches {total_lines} lines ({total_added}+, {total_removed}-). "
                "Large diffs are harder to review thoroughly; consider splitting into smaller PRs.",
            )
        )
    elif total_lines > 200:
        risks.append(
            (
                "Moderately large PR",
                f"This PR touches {total_lines} lines ({total_added}+, {total_removed}-). "
                "Consider whether it could be split.",
            )
        )

    # 2. Many files changed
    if len(files) > 20:
        risks.append(
            (
                "Many files changed",
                f"{len(files)} files modified. Broad scope increases risk of unintended side-effects.",
            )
        )

    # 3. Large individual files
    for f in files:
        f_total = f["added"] + f["removed"]
        if f_total > 300:
            risks.append(
                (
                    f"Large file: {f['path']}",
                    f"{f_total} lines changed ({f['added']}+, {f['removed']}-). "
                    "Large single-file changes are harder to audit.",
                )
            )

    # 4. Secret / credential exposure patterns
    secret_patterns = [
        (r'(?i)AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
        (r'(?i)secret\s*=\s*["\'][A-Za-z0-9+/=]{20,}["\']', "Generic secret assignment"),
        (r'(?i)password\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded password"),
        (r'(?i)api[_-]?key\s*[:=]\s*["\'][^"\']+["\']', "Hardcoded API key"),
        (r'(?i)token\s*[:=]\s*["\'][A-Za-z0-9._-]{20,}["\']', "Hardcoded token"),
        (r'(?i)-----BEGIN (RSA |EC )?PRIVATE KEY-----', "Private key embedded"),
        (r'ghp_[A-Za-z0-9]{36}', "GitHub personal access token"),
        (r'gho_[A-Za-z0-9]{36}', "GitHub OAuth access token"),
        (r'sk-[A-Za-z0-9]{20,}', "OpenAI API key"),
    ]
    for f in files:
        for i, line in enumerate(f["lines"]):
            if not line.startswith("+"):
                continue
            for pattern, label in secret_patterns:
                if re.search(pattern, line):
                    risks.append(
                        (
                            f"Possible secret leak in {f['path']}",
                            f"Line {line_number_from_hunks(f['lines'], i)} may contain a {label}. "
                            f"Check and remove before committing.",
                        )
                    )
                    break  # one warning per line max

    # 5. TODO / FIXME / HACK comments
    todo_count = 0
    for f in files:
        for line in f["lines"]:
            if line.startswith("+") and re.search(r'(?i)\b(TODO|FIXME|HACK|XXX|WORKAROUND)\b', line):
                todo_count += 1
    if todo_count > 0:
        risks.append(
            (
                f"Unresolved markers ({todo_count} found)",
                f"Found {todo_count} TODO/FIXME/HACK/XXX markers in the diff. "
                "These should be addressed or explicitly tracked.",
            )
        )

    # 6. Commented-out code
    commented_code = 0
    for f in files:
        for line in f["lines"]:
            stripped = line.lstrip()
            if line.startswith("+") and (
                stripped.startswith("// ") or stripped.startswith("# ")
                or stripped.startswith("/*") or stripped.startswith("* ")
                or stripped.startswith("<!--")
            ):
                # A heuristic: treat added comment lines as possibly commented-out
                pass
            # More specific: lines that are clearly commented-out code
            if line.startswith("+") and re.search(r'^\+\s*[#/]+\s*(console\.|print\(|def |function|var |let |const |import |from )', line):
                commented_code += 1
    if commented_code > 0:
        risks.append(
            (
                f"Commented-out code ({commented_code} lines)",
                "Commented-out code clutters the codebase. Remove it unless there is a clear reason.",
            )
        )

    # 7. Binary file changes (warning about binary files if present)
    binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz', '.exe', '.dll', '.so', '.pyc', '.woff', '.woff2', '.ttf', '.eot'}
    binary_files = [f for f in files if Path(f["path"]).suffix.lower() in binary_extensions]
    if binary_files:
        names = ", ".join(f["path"] for f in binary_files[:5])
        risks.append(
            (
                f"Binary file changes ({len(binary_files)})",
                f"Binary files are included: {names}. Binary diffs cannot be reviewed textually; "
                "verify these changes separately.",
            )
        )

    return risks


def line_number_from_hunks(lines: list[str], added_line_idx: int) -> int:
    """Try to infer a human-readable line number from the diff hunk headers."""
    current_line = 0
    for i, line in enumerate(lines):
        if i > added_line_idx:
            break
        hdr = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if hdr:
            current_line = int(hdr.group(1)) - 1
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current_line += 1
        elif line.startswith(" ") or line.startswith("-\+"):
            current_line += 1
    return current_line


def analyze_improvements(files):
    """Return a list of (suggestion_title, details) tuples."""
    improvements = []

    # 1. Missing error handling
    error_handling_keywords = {"try:", "except", "catch(", "catch (", ".catch(", "error"}
    has_error_handling = False
    for f in files:
        for line in f["lines"]:
            if line.startswith("+"):
                for kw in error_handling_keywords:
                    if kw in line.lower():
                        has_error_handling = True
                        break
            if has_error_handling:
                break
        if has_error_handling:
            break

    # Look for operations that typically need error handling
    risky_ops = 0
    risky_patterns = [r'open\(', r'\.read\(', r'\.write\(', r'\.send\(', r'request\.', r'\.get\(', r'\.post\(', r'fetch\(', r'\.connect\(', r'\.execute\(', r'exec\(', r'eval\(']
    for f in files:
        for line in f["lines"]:
            if line.startswith("+"):
                for pat in risky_patterns:
                    if re.search(pat, line.lower()):
                        risky_ops += 1
                        break

    if risky_ops > 0 and not has_error_handling:
        improvements.append(
            (
                "Missing error handling",
                f"Found {risky_ops} operations that may need error handling (file I/O, network, etc.) "
                "but no try/except or catch blocks were detected. Add proper error handling.",
            )
        )

    # 2. Missing tests
    has_test_changes = any(
        "test" in f["path"].lower() or f["path"].startswith("test")
        for f in files
    )
    if not has_test_changes and len(files) > 0:
        # Check if there are test files in the repo (not just in the PR)
        improvements.append(
            (
                "Missing test changes",
                "No test files were modified. Consider adding or updating tests to cover the changes.",
            )
        )

    # 3. Hardcoded values
    hardcoded_count = 0
    # Patterns that look like hardcoded magic numbers/strings
    hardcoded_patterns = [
        (r'[=:]\s*\d{4,}', "large magic number"),
        (r'(url|endpoint|host)\s*[:=]\s*["\']https?://[^"\']+["\']', "hardcoded URL"),
        (r'timeout\s*[:=]\s*\d+', "hardcoded timeout"),
        (r'port\s*[:=]\s*\d{4,5}', "hardcoded port"),
        (r'debug\s*=\s*(True|true)', "debug mode enabled"),
    ]
    for f in files:
        for line in f["lines"]:
            if line.startswith("+"):
                for pattern, label in hardcoded_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        hardcoded_count += 1
                        break

    if hardcoded_count > 0:
        improvements.append(
            (
                f"Hardcoded values ({hardcoded_count} found)",
                "Consider moving hardcoded values (URLs, ports, timeouts, magic numbers) "
                "to configuration or environment variables.",
            )
        )

    # 4. Large function / block detection (very basic heuristic)
    large_additions = [f for f in files if f["added"] > 100 and not f["path"].endswith((".json", ".yaml", ".yml", ".lock", ".svg", ".txt", ".md"))]
    if large_additions:
        names = ", ".join(f["path"] for f in large_additions[:3])
        improvements.append(
            (
                f"Large additions in {len(large_additions)} file(s)",
                f"{names}. Consider splitting large functions or classes for better maintainability.",
            )
        )

    # 5. No docstrings / comments on new code
    new_code_files = [f for f in files if f["added"] > 20 and not f["path"].endswith((".json", ".yaml", ".yml", ".lock", ".svg", ".txt", ".md"))]
    if new_code_files:
        improvements.append(
            (
                "Consider adding documentation",
                "New code additions may benefit from docstrings or inline comments explaining "
                "the rationale, especially for non-obvious logic.",
            )
        )

    return improvements


def determine_confidence(risks, improvements, files, total_added, total_removed):
    """Return 'Low', 'Medium', or 'High' confidence in the review."""
    total_lines = total_added + total_removed
    num_risks = len(risks)
    num_improvements = len(improvements)

    if total_lines > 1000 or num_risks > 5:
        return "Low"
    if num_risks == 0 and num_improvements <= 1 and total_lines < 100:
        return "High"
    if num_risks <= 2 and total_lines < 300:
        return "Medium"
    return "Low"


# ── Output ───────────────────────────────────────────────────────────────────


def generate_markdown(files, risks, improvements, confidence, pr_url):
    """Generate structured Markdown review report."""
    total_added, total_removed = total_changes(files)
    total_lines = total_added + total_removed
    file_types = count_file_types(files)

    lines = []
    lines.append(f"# PR Review: {pr_url}")
    lines.append("")

    # ── Summary ──
    lines.append("## Summary")
    summary_parts = []
    summary_parts.append(
        f"This PR modifies **{len(files)}** files across **{len(file_types)}** file types, "
        f"with **{total_added:,}** additions and **{total_removed:,}** deletions "
        f"({total_lines:,} total lines changed)."
    )

    # Determine primary nature of changes
    extensions = list(file_types.keys())
    primary_types = [e for e in extensions if e not in (".lock", ".json", ".yaml", ".yml", ".md", ".txt", "(none)")]
    if primary_types:
        summary_parts.append(
            f"The primary file types affected are {', '.join(primary_types[:5])}."
        )

    # Check if it's mostly config/doc
    if set(extensions).issubset({".md", ".txt", ".json", ".yaml", ".yml", ".cfg", ".ini"}):
        summary_parts.append("Changes are primarily in configuration, documentation, or data files.")
    else:
        summary_parts.append("Source code changes are present alongside potential configuration updates.")

    lines.append(" ".join(summary_parts))

    # ── Changed files table (as structured list, since Telegram doesn't support tables) ──
    lines.append("")
    lines.append("### Changed Files")
    lines.append("")
    lines.append("| File | + | - | Total |")
    lines.append("|------|---|---|-------|")
    for f in sorted(files, key=lambda x: -(x["added"] + x["removed"])):
        f_total = f["added"] + f["removed"]
        lines.append(f"| {f['path']} | {f['added']} | {f['removed']} | {f_total} |")
    lines.append("")

    # ── Risks ──
    lines.append("## Identified Risks")
    if not risks:
        lines.append("No specific risks identified.")
    else:
        for i, (title, detail) in enumerate(risks, 1):
            lines.append(f"### {i}. {title}")
            lines.append(detail)
            lines.append("")
    lines.append("")

    # ── Improvements ──
    lines.append("## Improvement Suggestions")
    if not improvements:
        lines.append("No specific improvements suggested.")
    else:
        for i, (title, detail) in enumerate(improvements, 1):
            lines.append(f"### {i}. {title}")
            lines.append(detail)
            lines.append("")
    lines.append("")

    # ── Confidence ──
    lines.append("## Confidence Score")
    icon = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    lines.append(f"**{icon.get(confidence, '⚪')} {confidence}**")
    confidence_notes = {
        "High": "Changes are small, well-scoped, with no significant risks detected.",
        "Medium": "Some risks or improvement areas were noted but the changes appear generally sound.",
        "Low": "Significant risks or very large changes make a detailed human review strongly recommended.",
    }
    lines.append(confidence_notes.get(confidence, ""))
    lines.append("")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — Analyze GitHub PR diffs programmatically."
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="Full GitHub PR URL, e.g. https://github.com/owner/repo/pull/123",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write output to file instead of stdout.",
    )
    args = parser.parse_args()

    token = load_github_token()
    owner, repo, pr_number = parse_pr_url(args.pr)

    # Fetch diff from GitHub
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    print(f"🔄 Fetching diff for {args.pr} ...", file=sys.stderr)
    diff_text = fetch(url, token)

    if not diff_text.strip():
        die("Received empty diff from GitHub API.")

    print(f"📊 Parsing diff ({len(diff_text):,} bytes) ...", file=sys.stderr)
    files = parse_diff(diff_text)

    if not files:
        die("No file changes detected in the PR diff.")

    # Analyze
    risks = analyze_risks(files)
    improvements = analyze_improvements(files)
    total_added, total_removed = total_changes(files)
    confidence = determine_confidence(risks, improvements, files, total_added, total_removed)

    # Generate report
    report = generate_markdown(files, risks, improvements, confidence, args.pr)

    if args.output:
        Path(args.output).write_text(report)
        print(f"✅ Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
