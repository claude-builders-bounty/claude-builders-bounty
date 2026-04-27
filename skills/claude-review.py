#!/usr/bin/env python3
"""
claude-review — Claude Code sub-agent for PR review.
Analyzes a GitHub PR diff and returns structured Markdown review.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

Requires:
    - GitHub personal access token (GH_TOKEN env var or gh CLI installed)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReviewResult:
    summary: str = ""
    risks: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)
    confidence: str = "Medium"
    files_changed: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    score: str = ""


def parse_pr_url(url: str) -> tuple:
    """Parse a PR URL into (owner, repo, pr_number)."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    m = re.search(pattern, url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the PR diff from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent/1.0",
    })
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        # Fallback: try gh CLI
        try:
            result = subprocess.run(
                ["gh", "pr", "diff", str(pr_number), "-R", f"{owner}/{repo}"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return result.stdout
        except Exception:
            pass
        raise RuntimeError(f"Failed to fetch PR diff: {e}")


def get_pr_info(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR metadata."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-agent/1.0",
    })
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "title": data.get("title", ""),
                "body": data.get("body", "")[:500],
                "state": data.get("state", ""),
                "author": data.get("user", {}).get("login", ""),
                "base": data.get("base", {}).get("ref", ""),
                "head": data.get("head", {}).get("ref", ""),
            }
    except:
        return {"title": f"PR #{pr_number}", "body": ""}


def analyze_diff(diff: str, pr_info: dict) -> ReviewResult:
    """Analyze the PR diff using heuristic rules."""
    result = ReviewResult()

    # Count stats
    lines = diff.split("\n")
    result.files_changed = sum(1 for line in lines if line.startswith("+++ ") or line.startswith("--- ")) // 2
    result.lines_added = sum(1 for line in lines if line.startswith("+") and not line.startswith("+++"))
    result.lines_removed = sum(1 for line in lines if line.startswith("-") and not line.startswith("---"))

    # Generate summary
    result.summary = (
        f"**PR:** {pr_info.get('title', 'Unknown')}\n"
        f"**Branch:** `{pr_info.get('head', '?')}` → `{pr_info.get('base', '?')}`\n"
        f"**Changes:** {result.files_changed} files, "
        f"+{result.lines_added}/-{result.lines_removed} lines\n"
        f"**Author:** @{pr_info.get('author', 'unknown')}"
    )

    # Check for specific patterns
    # 1. TODO/FIXME comments
    todos = [line.strip() for line in lines if "TODO" in line or "FIXME" in line or "HACK" in line]
    if todos:
        result.risks.append(
            f"⚠️ Contains {len(todos)} TODO/FIXME/HACK comment(s) — may indicate incomplete work"
        )

    # 2. Debug / test code
    debug_patterns = ["print(", "console.log(", "logger.debug(", "var_dump(", "p db"]
    debug_lines = []
    for line in lines:
        stripped = line.strip()
        if any(pattern in stripped.lower() for pattern in debug_patterns):
            debug_lines.append(stripped[:80])
    if debug_lines:
        result.suggestions.append(
            f"🔍 Remove debug/logging statements: {len(debug_lines)} found"
        )

    # 3. Large files
    file_sizes = {}
    current_file = ""
    for line in lines:
        if line.startswith("+++ b/"):
            current_file = line[6:]
            file_sizes[current_file] = 0
        elif current_file and (line.startswith("+") or line.startswith("-")):
            file_sizes[current_file] = file_sizes.get(current_file, 0) + 1
    large_files = {f: s for f, s in file_sizes.items() if s > 200}
    if large_files:
        for f, s in large_files.items():
            result.suggestions.append(
                f"📦 Large diff in `{f}` ({s} lines) — consider splitting into smaller PRs"
            )

    # 4. No test changes
    has_tests = any("test" in line.lower() or "spec" in line.lower() or "__test" in line for line in lines)
    if not has_tests and result.files_changed > 0:
        result.risks.append("🧪 No test files detected — verify test coverage")

    # 5. Security concerns
    security_patterns = {
        "SQL injection risk": [r"execute\(.*\+", r"query\(.*f\"", r"raw_query\("],
        "Hardcoded secret": [r"(api_key|apikey|secret|password|token)\s*[=:]\s*['\"](?!ENV)", re.IGNORECASE],
        "eval usage": [r"\beval\s*\(", r"\bexec\s*\(", r"\b__import__\s*\("],
    }
    for risk_name, patterns in security_patterns.items():
        for pat in patterns:
            flags = re.IGNORECASE if isinstance(patterns[-1], int) else 0
            matches = re.findall(pat, diff, flags)
            if matches:
                result.risks.append(f"🔴 Potential {risk_name} detected ({len(matches)} occurrence(s))")

    # 6. No documentation for new public APIs
    if "def " in diff or "pub fn " in diff or "export function " in diff or "export const " in diff:
        doc_patterns = ["\"\"\"", "'''", "/**", "///", "//!"] + (["@param", "@return"] if result.files_changed > 1 else [])
        has_docs = any(p in diff for p in doc_patterns)
        if not has_docs:
            result.suggestions.append(
                "📝 New functions/APIs without documentation — consider adding docstrings"
            )

    # Confidence score
    if result.files_changed <= 3 and result.lines_added <= 100:
        result.confidence = "High"
    elif result.files_changed <= 10 and result.lines_added <= 500:
        result.confidence = "Medium"
    else:
        result.confidence = "Low"

    # Overall score
    risk_count = len(result.risks)
    if risk_count == 0:
        result.score = "✅ LGTM — no issues found"
    elif risk_count <= 2:
        result.score = "🟡 Minor concerns — address suggestions before merging"
    else:
        result.score = "🔴 Review required — address risks before merging"

    # If no specific patterns matched, add general suggestions
    if not result.suggestions:
        if result.lines_added > 50:
            result.suggestions.append("💡 Consider adding unit tests for edge cases")
        if result.files_changed > 5:
            result.suggestions.append("💡 Changes span multiple files — verify integration points")

    return result


def format_markdown(result: ReviewResult, pr_url: str) -> str:
    """Format the review as structured Markdown."""
    md = []
    md.append(f"## 🤖 Automated PR Review — [{pr_url.split('/')[-1]}]({pr_url})")
    md.append("")
    md.append(f"**Confidence:** {result.confidence}  |  **Score:** {result.score}")
    md.append("")
    md.append("---")
    md.append("")
    md.append("### 📋 Summary")
    md.append("")
    md.append(result.summary)
    md.append("")
    md.append(f"**Total:** +{result.lines_added} / -{result.lines_removed} across {result.files_changed} file(s)")
    md.append("")

    if result.risks:
        md.append("### ⚠️ Risks")
        md.append("")
        for r in result.risks:
            md.append(f"- {r}")
        md.append("")

    if result.suggestions:
        md.append("### 💡 Improvement Suggestions")
        md.append("")
        for s in result.suggestions:
            md.append(f"- {s}")
        md.append("")

    md.append("---")
    md.append("")
    md.append("*Generated by claude-review agent*")
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR")
    parser.add_argument("--pr", required=True, help="PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--output", help="Output file (default: print to stdout)")
    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr)
    print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    pr_info = get_pr_info(owner, repo, pr_number)
    diff = get_pr_diff(owner, repo, pr_number)

    print(f"📊 Analyzing {len(diff)} bytes of diff...", file=sys.stderr)
    result = analyze_diff(diff, pr_info)
    review = format_markdown(result, args.pr)

    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(review)


if __name__ == "__main__":
    main()
