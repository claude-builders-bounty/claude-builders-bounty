#!/usr/bin/env python3
"""
Claude Code PR Review Agent — analyzes PR diffs and returns structured reviews.

Usage:
  python pr_review.py --pr https://github.com/owner/repo/pull/123
  python pr_review.py --pr owner/repo/123
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_pr_url(pr_url: str) -> tuple[str, str, str]:
    """Parse PR URL or shorthand into owner, repo, number."""
    if "://" in pr_url:
        parts = pr_url.rstrip("/").split("/")
        return parts[-4], parts[-3], parts[-1]
    else:
        parts = pr_url.split("/")
        return parts[0], parts[1], parts[2]


def fetch_pr_diff(owner: str, repo: str, pr_num: str) -> str:
    """Fetch PR diff via GitHub API."""
    import urllib.request
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching PR: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_metadata(owner: str, repo: str, pr_num: str) -> dict:
    """Fetch PR title, description, changed files."""
    import urllib.request
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "claude-review-agent/1.0"}
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching PR metadata: {e}", file=sys.stderr)
        return {}


def analyze_diff(diff: str) -> dict:
    """
    Analyze a PR diff and return structured review.
    Uses pattern-based analysis (no external API calls).
    """
    files_changed = []
    current_file = ""
    additions = 0
    deletions = 0
    risks = []
    suggestions = []

    # Analysis patterns
    SECRET_PATTERNS = [
        (r"(?i)(api[_-]?key|secret|token|password|credential|auth[_-]?key)\s*[:=]\s*['\"][^'\"]+['\"]", "Possible credential hardcoded"),
        (r"(?i)(-----BEGIN\s+(RSA|EC|PRIVATE|OPENSSH)\s+KEY-----)", "Private key detected in source"),
        (r"(?i)(ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{36}", "GitHub token detected — possible credential leak"),
    ]
    SECURITY_WEAKNESSES = [
        (r"(?i)(eval|exec)\s*\(", "Use of eval/exec — potential code injection risk"),
        (r"(?i)(innerHTML|outerHTML|dangerouslySetInnerHTML)", "Direct HTML injection — potential XSS vector"),
        (r"(?i)(SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*=\s*['\"].*\+|\bf-string.*SELECT)", "SQL injection risk — use parameterized queries"),
        (r"\.env", "Environment file modification detected"),
        (r"(?i)(TODO|FIXME|HACK|XXX)", "TODO/FIXME found — incomplete work"),
        (r"(?i)(console\.log|print\s*\()", "Debug logging left in code"),
        (r"(?i)(http://)", "HTTP URL detected — use HTTPS"),
        (r"(?i)(except:|catch\s*\{|catch\s*\(.*\)\s*\{)", "Empty exception handler — consider logging the error"),
    ]
    HARDCODED_PATTERNS = [
        (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
        (r"localhost|127\.0\.0\.1", "Hardcoded localhost address"),
        (r"(?i)(db_host|database_url|connection_string)\s*[:=]\s*['\"][^'\"]+['\"]", "Hardcoded connection string"),
        (r"(?i)(ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{36}", "Hardcoded GitHub credential"),
    ]

    for line in diff.split("\n"):
        # Track file changes
        fm = re.match(r"^\+\+\+\s+(?:b/)?(.+)", line)
        if fm:
            current_file = fm.group(1)
            if current_file not in files_changed:
                files_changed.append(current_file)

        # Count additions/deletions
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

        # Risk detection
        for pat, desc in SECRET_PATTERNS:
            if re.search(pat, line):
                risks.append(f"[CRITICAL] Possible secret exposure in `{current_file}`: {desc}")
        for pat, desc in SECURITY_WEAKNESSES:
            if re.search(pat, line) and not line.startswith("-"):
                risks.append(f"[MEDIUM] {desc} in `{current_file}`")
        for pat, desc in HARDCODED_PATTERNS:
            if re.search(pat, line) and not line.startswith("-"):
                risks.append(f"[HIGH] {desc} in `{current_file}`")

    # Generate suggestions
    if additions > 200:
        suggestions.append("Large PR — consider splitting into smaller, focused PRs for easier review")
    if additions > 0 and deletions == 0:
        suggestions.append("PR only adds code, no deletions — verify no dead code left behind")
    if len(files_changed) > 10:
        suggestions.append(f"PR touches {len(files_changed)} files — may indicate scope creep")

    # Confidence scoring
    total_lines = additions + deletions
    if total_lines < 20:
        confidence = "High"
    elif total_lines < 100:
        if len(risks) > 3:
            confidence = "Medium"
        else:
            confidence = "High"
    else:
        if len(risks) > 5:
            confidence = "Low"
        elif len(risks) > 2:
            confidence = "Medium"
        else:
            confidence = "Medium"

    summary_lines = [
        f"Changes **{additions} additions, {deletions} deletions** across **{len(files_changed)} files**.",
        f"Primary files: {', '.join(files_changed[:5])}",
    ]
    if len(files_changed) > 5:
        summary_lines.append(f"(+{len(files_changed) - 5} more)")

    return {
        "summary": " ".join(summary_lines),
        "files_changed": files_changed,
        "additions": additions,
        "deletions": deletions,
        "risks": list(set(risks)),
        "suggestions": suggestions,
        "confidence": confidence,
    }


def format_review(result: dict, meta: dict) -> str:
    """Format the review as structured Markdown."""
    lines = []
    lines.append("## PR Review\n")
    if meta.get("title"):
        lines.append(f"**Title:** {meta['title']}\n")
    lines.append("### Summary")
    lines.append("")
    lines.append(result["summary"])
    lines.append("")

    lines.append("### Identified Risks")
    lines.append("")
    if result["risks"]:
        for r in result["risks"]:
            lines.append(f"- {r}")
    else:
        lines.append("_No significant risks identified._")
    lines.append("")

    lines.append("### Improvement Suggestions")
    lines.append("")
    if result["suggestions"]:
        for s in result["suggestions"]:
            lines.append(f"- {s}")
    else:
        lines.append("_No suggestions at this time._")
    lines.append("")

    lines.append("### Stats")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Files Changed | {len(result['files_changed'])} |")
    lines.append(f"| Additions | {result['additions']} |")
    lines.append(f"| Deletions | {result['deletions']} |")
    lines.append(f"| Confidence | **{result['confidence']}** |")
    lines.append("")

    return "\n".join(lines)


def review_pr(pr_url: str, output_file: str | None = None) -> str:
    """Full PR review workflow."""
    owner, repo, pr_num = parse_pr_url(pr_url)
    print(f"Fetching PR #{pr_num} from {owner}/{repo}...", file=sys.stderr)

    meta = fetch_pr_metadata(owner, repo, pr_num)
    diff = fetch_pr_diff(owner, repo, pr_num)
    result = analyze_diff(diff)
    review = format_review(result, meta)

    if output_file:
        Path(output_file).write_text(review, encoding="utf-8")
        print(f"Review written to {output_file}", file=sys.stderr)
    else:
        print(review)

    return review


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR and return structured feedback")
    parser.add_argument("--pr", required=True, help="PR URL (https://github.com/owner/repo/pull/123) or owner/repo/123")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()
    review_pr(args.pr, args.output)


if __name__ == "__main__":
    main()
