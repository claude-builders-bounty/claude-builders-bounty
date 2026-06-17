#!/usr/bin/env python3
"""claude-review - Analyze a GitHub PR and return a structured Markdown review.

Usage:
  python claude-review.py --pr https://github.com/owner/repo/pull/123

Output: Structured Markdown with summary, risks, suggestions, and confidence.
"""

import argparse, json, os, re, sys
from collections import Counter
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def fetch(url: str, token: str = "") -> str:
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    try:
        with urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except HTTPError as e:
        print(f"Error fetching {url}: {e.code}", file=sys.stderr)
        sys.exit(1)


def parse_pr_url(url: str) -> tuple:
    """Extract owner, repo, PR number from a GitHub PR URL."""
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        print("Error: Invalid PR URL. Expected: https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)
    return m.group(1), m.group(2), m.group(3)


def analyze_diff(diff: str) -> dict:
    """Analyze a git diff and return structured analysis."""
    if not diff or not diff.strip():
        return {"summary": "No changes detected.", "risks": [], "suggestions": [], "confidence": "Low"}

    lines = diff.split("\n")
    added = deleted = 0
    files_changed = set()
    risky_patterns = []
    file_types = Counter()
    current_file = ""

    for line in lines:
        if line.startswith("+++ b/"):
            current_file = line[6:]
            files_changed.add(current_file)
            ext = os.path.splitext(current_file)[1]
            if ext:
                file_types[ext] += 1
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
            stripped = line[1:].strip().lower()
            if stripped in ("console.log(", "console.log"):
                risky_patterns.append(f"console.log in {current_file}")
            if "todo" in stripped and "fix" in stripped:
                risky_patterns.append(f"TODO/FIXME in {current_file}")
            if "password" in stripped or "secret" in stripped or "api_key" in stripped:
                risky_patterns.append(f"Potential secret in {current_file}")
        elif line.startswith("-") and not line.startswith("---"):
            deleted += 1

    total_changes = added + deleted
    risk_level = "Low"
    risks = []
    suggestions = []

    if total_changes > 500:
        risk_level = "Medium"
        risks.append("Large PR (>500 lines) - consider splitting into smaller PRs")
    if len(files_changed) > 15:
        risk_level = "Medium"
        risks.append(f"Many files changed ({len(files_changed)})")
    for p in risky_patterns:
        risk_level = "Medium"
        risks.append(p)
    if added > 0 and deleted == 0:
        suggestions.append("Consider if any old code should be removed alongside this addition")
    if len(files_changed) == 1:
        suggestions.append("Well-scoped change - single file modified")

    file_types_str = ", ".join(f"{ext} ({count})" for ext, count in file_types.most_common(5)) if file_types else "N/A"

    summary_lines = [
        f"**{len(files_changed)} file(s)** changed across **{total_changes} line(s)** (+{added}/-{deleted}).",
        f"**File types:** {file_types_str}" if file_types_str != "N/A" else "",
    ]

    confidence = "High" if total_changes < 100 else "Medium" if total_changes < 500 else "Low"

    return {
        "summary": "\n".join(filter(None, summary_lines)),
        "risks": risks if risks else ["No significant risks identified."],
        "suggestions": suggestions if suggestions else ["PR looks clean."],
        "confidence": confidence,
        "stats": {"files": len(files_changed), "added": added, "deleted": deleted, "total": total_changes},
    }


def format_review(analysis: dict, pr_number: str, pr_url: str) -> str:
    """Format analysis as structured Markdown."""
    lines = [f"## PR Review: #{pr_number}", "", f"PR URL: {pr_url}", ""]
    lines.append("### Summary of Changes")
    lines.append("")
    lines.append(analysis["summary"])
    lines.append("")
    lines.append("### Identified Risks")
    lines.append("")
    for risk in analysis["risks"]:
        lines.append(f"- {risk}")
    lines.append("")
    lines.append("### Improvement Suggestions")
    lines.append("")
    for sug in analysis["suggestions"]:
        lines.append(f"- {sug}")
    lines.append("")
    lines.append(f"### Confidence Score: **{analysis['confidence']}**")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze a GitHub PR")
    parser.add_argument("--pr", required=True, help="PR URL (https://github.com/owner/repo/pull/123)")
    parser.add_argument("--token", default="", help="GitHub token for private repos")
    args = parser.parse_args()

    owner, repo, number = parse_pr_url(args.pr)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}.diff"

    diff = fetch(diff_url, args.token)
    analysis = analyze_diff(diff)
    review = format_review(analysis, number, args.pr)
    print(review)


if __name__ == "__main__":
    main()
