#!/usr/bin/env python3
"""
Claude Code PR Review Agent
Bounty: claude-builders-bounty/claude-builders-bounty #4 ($150)

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr owner/repo/123

Analyzes a PR diff and outputs a structured Markdown review comment.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ReviewResult:
    summary: str = ""
    risks: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: str = "Medium"  # Low / Medium / High
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0


def parse_pr_url(url: str):
    """Parse PR URL or shorthand into (owner, repo, pr_number)."""
    # Full URL: https://github.com/owner/repo/pull/123
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    # Shorthand: owner/repo/123
    m = re.match(r'([^/]+)/([^/]+)/(\d+)', url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(f"Cannot parse PR reference: {url}")


def run_gh(args: List[str]) -> str:
    """Run a gh CLI command and return stdout."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr}")
    return result.stdout


def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the PR diff."""
    return run_gh(["api", f"repos/{owner}/{repo}/pulls/{pr_number}",
                   "-H", "Accept: application/vnd.github.v3.diff"])


def get_pr_info(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR metadata."""
    out = run_gh(["api", f"repos/{owner}/{repo}/pulls/{pr_number}"])
    return json.loads(out)


def analyze_diff(diff: str, pr_info: dict) -> ReviewResult:
    """Analyze the diff and produce a structured review."""
    result = ReviewResult()
    result.additions = pr_info.get("additions", 0)
    result.deletions = pr_info.get("deletions", 0)
    result.files_changed = pr_info.get("changed_files", 0)

    lines = diff.split('\n')
    current_file = ""
    added_lines = []
    removed_lines = []

    for line in lines:
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("--- a/"):
            pass
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines.append((current_file, line[1:]))
        elif line.startswith("-") and not line.startswith("---"):
            removed_lines.append((current_file, line[1:]))

    # --- Risk Detection ---
    risk_patterns = [
        (r'\b(eval|exec)\s*\(', "Use of eval/exec — potential code injection risk"),
        (r'\bsubprocess\.(call|run|Popen)\s*\(', "Subprocess call — ensure inputs are sanitized"),
        (r'\bSQL\b.*\b(f|string_format|%)', "Potential SQL injection — use parameterized queries"),
        (r'\bpassword\b\s*=\s*["\']', "Hardcoded password detected"),
        (r'\bapi_key\b\s*=\s*["\']', "Hardcoded API key detected"),
        (r'\bsecret\b\s*=\s*["\']', "Hardcoded secret detected"),
        (r'\btoken\b\s*=\s*["\'][^"\']{10,}', "Hardcoded token detected"),
        (r'\bchmod\s+777', "Overly permissive file permissions (chmod 777)"),
        (r'\bTODO\b', "TODO left in code — consider resolving before merge"),
        (r'\bFIXME\b', "FIXME left in code — known issue not addressed"),
        (r'\bexcept\s*:', "Bare except clause — may silently swallow errors"),
        (r'\bexcept\s+Exception\s*:', "Broad exception handler — may hide specific errors"),
        (r'\bprint\s*\(', "Print statement in production code — use logging"),
        (r'\bdebug\s*=\s*True', "Debug mode enabled — should be False in production"),
        (r'\bopen\s*\([^)]*\)(?!\s+as)', "File open without context manager — resource leak risk"),
    ]

    for filepath, line in added_lines:
        for pattern, message in risk_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                risk = f"`{filepath}`: {message}"
                if risk not in result.risks:
                    result.risks.append(risk)

    # Large PR risk
    if result.additions > 500:
        result.risks.append(f"Large PR ({result.additions} additions) — consider splitting into smaller PRs")

    # --- Suggestion Detection ---
    suggestion_patterns = [
        (r'\bif\s+\w+\s+is\s+None\b', "Consider using `if x is None` pattern consistently, or use early returns"),
        (r'\bfor\s+\w+\s+in\s+range\(len\(', "Consider using enumerate() instead of range(len(...))"),
        (r'\.append\([^)]*\)\s*$', "Consider using list comprehension for building lists"),
        (r'\btime\.sleep\(', "Blocking sleep — consider async alternatives if in async context"),
        (r'\bopen\s*\([^)]*[\'\"]w', "File write operation — ensure proper error handling and atomic writes"),
        (r'\bjson\.loads?\([^)]*\)', "JSON parse — ensure proper error handling for malformed input"),
    ]

    for filepath, line in added_lines:
        for pattern, message in suggestion_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                suggestion = f"`{filepath}`: {message}"
                if suggestion not in result.suggestions:
                    result.suggestions.append(suggestion)

    # General suggestions based on PR size
    if result.files_changed > 10:
        result.suggestions.append("Many files changed — consider splitting into focused PRs")

    if not result.risks and not result.suggestions:
        result.suggestions.append("Code looks clean. Consider adding tests for the new functionality.")

    # --- Summary ---
    title = pr_info.get("title", "Untitled PR")
    result.summary = (
        f"This PR ({title}) changes {result.files_changed} file(s) "
        f"(+{result.additions}/-{result.deletions}). "
    )

    if result.risks:
        result.summary += f"Found {len(result.risks)} potential risk(s). "
    else:
        result.summary += "No significant risks detected. "

    if result.suggestions:
        result.summary += f"Has {len(result.suggestions)} improvement suggestion(s)."

    # --- Confidence ---
    diff_size = len(diff)
    if diff_size < 500:
        result.confidence = "High"
    elif diff_size < 5000:
        result.confidence = "Medium"
    else:
        result.confidence = "Low"

    return result


def format_review(review: ReviewResult, pr_url: str) -> str:
    """Format the review as structured Markdown."""
    md = f"""## 🤖 Automated PR Review

**PR**: {pr_url}
**Files changed**: {review.files_changed} | **Additions**: +{review.additions} | **Deletions**: -{review.deletions}

### Summary

{review.summary}

### ⚠️ Identified Risks

"""
    if review.risks:
        for risk in review.risks:
            md += f"- {risk}\n"
    else:
        md += "No significant risks identified.\n"

    md += "\n### 💡 Improvement Suggestions\n\n"
    if review.suggestions:
        for suggestion in review.suggestions[:10]:  # Cap at 10
            md += f"- {suggestion}\n"
    else:
        md += "No suggestions — code looks good!\n"

    md += f"\n### 🎯 Confidence Score: **{review.confidence}**\n"
    md += "\n---\n*Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty)*\n"

    return md


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Agent")
    parser.add_argument("--pr", required=True, help="PR URL or shorthand (owner/repo/123)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--comment", action="store_true", help="Post review as PR comment")
    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr)
    pr_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}"

    print(f"📋 Reviewing {pr_url}...", file=sys.stderr)

    # Fetch PR data
    diff = get_pr_diff(owner, repo, pr_number)
    pr_info = get_pr_info(owner, repo, pr_number)

    # Analyze
    review = analyze_diff(diff, pr_info)

    # Format
    markdown = format_review(review, pr_url)

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(markdown)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(markdown)

    # Post as comment if requested
    if args.comment:
        body_file = "/tmp/claude_review_body.txt"
        with open(body_file, 'w') as f:
            f.write(markdown)
        run_gh(["issue", "comment", str(pr_number),
                "--repo", f"{owner}/{repo}",
                "--body-file", body_file])
        print(f"✅ Review posted as comment on {pr_url}", file=sys.stderr)


if __name__ == "__main__":
    main()