#!/usr/bin/env python3
"""
pr-reviewer.py — Claude Code sub-agent for PR review

Analyzes a GitHub Pull Request diff and generates a structured Markdown review.

Usage:
  python3 pr-reviewer.py https://github.com/owner/repo/pull/123
  python3 pr-reviewer.py path/to/diff.patch
  python3 pr-reviewer.py --stdin             # Read diff from stdin

Output:
  Structured Markdown with: summary, risks, suggestions, confidence score
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from collections import Counter

# ── GitHub API ──────────────────────────────────────────────────────────────

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")

def fetch_pr_diff(pr_url: str) -> tuple[str, str, str]:
    """Fetch the diff from a GitHub PR URL. Returns (diff_text, repo, pr_number)."""
    # Parse URL: https://github.com/owner/repo/pull/123
    match = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    
    owner, repo, pr_num = match.group(1), match.group(2), match.group(3)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-pr-reviewer/1.0"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    
    req = urllib.request.Request(api_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            diff = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR: {e.code} {e.reason}", file=sys.stderr)
        if e.code == 403:
            print("Hint: Set GITHUB_TOKEN env var for authenticated requests", file=sys.stderr)
        sys.exit(1)
    
    return diff, f"{owner}/{repo}", pr_num


def read_diff_from_file(path: str) -> str:
    """Read diff from a local file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


# ── Diff Analysis ──────────────────────────────────────────────────────────

def parse_diff(diff: str) -> dict:
    """Parse a diff and extract structured information."""
    result = {
        "files_changed": [],
        "total_additions": 0,
        "total_deletions": 0,
        "file_extensions": Counter(),
        "has_tests": False,
        "has_comments": False,
        "has_todos": False,
        "has_debug_code": False,
        "has_secrets": False,
        "lines": [],
        "risks": [],
    }
    
    current_file = None
    
    for line in diff.split("\n"):
        if line.startswith("+++ b/"):
            current_file = line[6:]
            if current_file:
                result["files_changed"].append(current_file)
                ext = os.path.splitext(current_file)[1]
                if ext:
                    result["file_extensions"][ext] += 1
        elif line.startswith("@@"):
            match = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
            if match:
                added = int(match.group(2 or 1))
                result["total_additions"] += added
        elif line.startswith("+") and not line.startswith("+++"):
            result["lines"].append(("added", line[1:], current_file))
            # Security checks
            content = line[1:].lower()
            if any(kw in content for kw in ["password", "secret", "api_key", "token=", "private_key"]):
                result["has_secrets"] = True
                result["risks"].append(f"Potential secret exposure in {current_file}")
            if "debugger" in content or "console.log" in content or "print(" in content:
                result["has_debug_code"] = True
            if "todo" in content or "fixme" in content or "hack" in content:
                result["has_todos"] = True
        elif line.startswith("-") and not line.startswith("---"):
            result["lines"].append(("deleted", line[1:], current_file))
            result["total_deletions"] += 1
    
    # Check for test files
    for f in result["files_changed"]:
        if re.search(r'(test|spec|__tests__|\.test\.)', f, re.IGNORECASE):
            result["has_tests"] = True
    
    return result


def generate_review(diff: str, parsed: dict, repo: str, pr_number: str) -> str:
    """Generate a structured Markdown review."""
    
    summary_parts = []
    
    # File count
    n_files = len(parsed["files_changed"])
    summary_parts.append(f"This PR modifies **{n_files}** file{'s' if n_files != 1 else ''}")
    
    # Line count
    if parsed["total_additions"] > 0 or parsed["total_deletions"] > 0:
        summary_parts.append(
            f"with **+{parsed['total_additions']}** / **-{parsed['total_deletions']}** lines of change"
        )
    
    # File types
    exts = parsed["file_extensions"]
    if exts:
        ext_str = ", ".join(f"`{ext}`" for ext, count in exts.most_common(5))
        summary_parts.append(f"involving {ext_str}")
    
    # Test presence
    test_note = ""
    if parsed["has_tests"]:
        test_note = "Test files are included in this PR."
    else:
        test_note = "No test files detected in this PR."
    
    # Risks
    risks = list(parsed["risks"])
    if parsed["has_debug_code"]:
        risks.append("Debug code (console.log, print, debugger) detected — should be removed before merge")
    if parsed["has_todos"]:
        risks.append("TODO/FIXME markers found — unresolved tasks should be addressed")
    if parsed["has_secrets"]:
        risks.append("⚠️ CRITICAL: Potential secrets/tokens detected in diff — check immediately!")
    
    # Suggestions
    suggestions = []
    if parsed["total_additions"] > 500:
        suggestions.append("Large PR (>500 additions) — consider splitting into smaller, focused PRs")
    if n_files > 15:
        suggestions.append("Many files changed (>15) — verify scope is cohesive")
    
    if parsed["has_tests"]:
        suggestions.append("✅ Good practice adding tests — ensure coverage is adequate")
    else:
        suggestions.append("Consider adding tests to verify the changes")
    
    # Confidence score
    confidence = "High"
    if n_files > 20 or parsed["total_additions"] > 1000:
        confidence = "Medium"
    if parsed["has_secrets"]:
        confidence = "Low"
    
    # ── Build output ──
    lines = []
    lines.append("# 🔍 Pull Request Review")
    lines.append("")
    lines.append(f"**Repository:** {repo}")
    lines.append(f"**PR:** #{pr_number}")
    lines.append("")
    
    # Summary
    lines.append("## 📋 Summary")
    lines.append("")
    lines.append(" ".join(summary_parts) + ".")
    if test_note:
        lines.append("")
        lines.append(test_note)
    lines.append("")
    
    # Files changed
    lines.append("### Files Changed")
    lines.append("")
    for f in parsed["files_changed"]:
        lines.append(f"- `{f}`")
    lines.append("")
    
    # Risks
    lines.append("## ⚠️ Risks Identified")
    lines.append("")
    if risks:
        for risk in risks:
            lines.append(f"- {risk}")
    else:
        lines.append("- No significant risks identified")
    lines.append("")
    
    # Suggestions
    lines.append("## 💡 Improvement Suggestions")
    lines.append("")
    if suggestions:
        for suggestion in suggestions:
            lines.append(f"- {suggestion}")
    else:
        lines.append("- The PR looks well-structured. No specific suggestions.")
    lines.append("")
    
    # Confidence
    score_emoji = {"Low": "🔴", "Medium": "🟡", "High": "🟢"}
    lines.append("## ✅ Confidence Score")
    lines.append("")
    lines.append(f"**{score_emoji.get(confidence, '⚪')} {confidence}**")
    lines.append("")
    lines.append("| Factor | Detail |")
    lines.append("|--------|--------|")
    lines.append(f"| Size | {n_files} files, +{parsed['total_additions']}/-{parsed['total_deletions']} lines |")
    lines.append(f"| Tests | {'✅ Present' if parsed['has_tests'] else '❌ Not detected'} |")
    lines.append(f"| Security | {'⚠️ Issues found' if parsed['has_secrets'] else '✅ No obvious issues'} |")
    lines.append(f"| Debug code | {'⚠️ Present' if parsed['has_debug_code'] else '✅ None detected'} |")
    lines.append("")
    
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Review a GitHub Pull Request")
    parser.add_argument("input", nargs="?", help="PR URL or path to .patch file")
    parser.add_argument("--stdin", action="store_true", help="Read diff from stdin")
    parser.add_argument("--output", "-o", help="Write output to file (default: stdout)")
    args = parser.parse_args()
    
    # Get diff
    repo, pr_number = "unknown", "0"
    diff = ""
    
    if args.stdin:
        diff = sys.stdin.read()
    elif args.input:
        if args.input.startswith("https://github.com/") and "/pull/" in args.input:
            print(f"Fetching PR diff from {args.input}...", file=sys.stderr)
            diff, repo, pr_number = fetch_pr_diff(args.input)
        else:
            diff = read_diff_from_file(args.input)
    else:
        parser.print_help()
        sys.exit(1)
    
    if not diff.strip():
        print("Error: Empty diff", file=sys.stderr)
        sys.exit(1)
    
    # Analyze
    parsed = parse_diff(diff)
    review = generate_review(diff, parsed, repo, pr_number)
    
    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(review)


if __name__ == "__main__":
    main()
