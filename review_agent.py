#!/usr/bin/env python3
"""PR Review Agent - Analyzes GitHub PR diffs and returns structured feedback.

Usage:
    python3 review_agent.py --pr https://github.com/owner/repo/pull/123
    python3 review_agent.py --diff /path/to/diff.patch

Requires: pip install requests
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.parse


def fetch_pr_info(pr_url):
    """Extract owner/repo/pull_number from PR URL and fetch diff."""
    match = re.match(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError(f"Invalid PR URL: {pr_url}")

    owner, repo, pr_num = match.group(1), match.group(2), match.group(3)

    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {"Accept": "application/vnd.github.v3.diff", "User-Agent": "claude-review-agent"}

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(diff_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        diff = resp.read().decode("utf-8")

    # Also fetch PR metadata
    headers["Accept"] = "application/vnd.github.v3+json"
    req2 = urllib.request.Request(diff_url, headers=headers)
    with urllib.request.urlopen(req2) as resp2:
        meta = json.loads(resp2.read())

    return {
        "title": meta["title"],
        "description": meta.get("body", ""),
        "author": meta["user"]["login"],
        "additions": meta.get("additions", 0),
        "deletions": meta.get("deletions", 0),
        "files_changed": meta.get("changed_files", 0),
        "diff": diff
    }


def analyze_diff(pr_info):
    """Analyze the PR diff and generate structured feedback."""
    diff = pr_info["diff"]
    findings = {
        "summary": "",
        "risks": [],
        "improvements": [],
        "confidence": "High"
    }

    # Generate summary
    summary_parts = []
    summary_parts.append(f"PR #{pr_info['title']} by @{pr_info['author']}")
    summary_parts.append(f"Changes: +{pr_info['additions']}/-{pr_info['deletions']} across {pr_info['files_changed']} files")

    # Analyze for common issues
    risks = []
    improvements = []

    # Check for common risk patterns
    risk_patterns = [
        (r"TODO|FIXME|HACK|XXX", "Contains TODO/FIXME/HACK comments that should be addressed"),
        (r"print\(|console\.log|printf", "Contains debug print statements"),
        (r"except:|catch\s*{", "Broad exception catching without specific handling"),
        (r"password|secret|token|credential", "Potential credential exposure in diff"),
        (r"DELETE FROM|DROP TABLE|TRUNCATE", "Destructive database operation detected"),
        (r"git push --force|git push -f", "Force push in code path"),
        (r"eval\(|exec\(|__import__", "Dynamic code execution detected"),
    ]

    for pattern, risk_desc in risk_patterns:
        matches = re.findall(pattern, diff, re.IGNORECASE)
        if matches:
            risks.append(risk_desc)

    # Check for missing tests
    if "test" not in diff.lower() and pr_info["files_changed"] > 3:
        improvements.append("Consider adding tests for the changes")

    # Check diff size
    if pr_info["additions"] > 500:
        improvements.append("Large PR (>500 lines added). Consider breaking into smaller PRs")
        findings["confidence"] = "Medium"
    elif pr_info["additions"] < 10 and pr_info["files_changed"] > 3:
        improvements.append("Small changes across many files - verify consistency")

    if not risks:
        risks.append("No critical risks identified")

    findings["summary"] = "
".join(summary_parts)
    findings["risks"] = risks
    findings["improvements"] = improvements
    return findings


def format_review(findings):
    """Format findings as structured Markdown."""
    lines = []
    lines.append("## PR Review")
    lines.append("")
    lines.append("### Summary")
    lines.append(findings["summary"])
    lines.append("")
    lines.append("### Identified Risks")
    for risk in findings["risks"]:
        lines.append(f"- {risk}")
    lines.append("")
    lines.append("### Improvement Suggestions")
    for imp in findings["improvements"]:
        lines.append(f"- {imp}")
    else:
        lines.append("- No specific improvements needed")
    lines.append("")
    lines.append(f"### Confidence Score: **{findings['confidence']}**")
    return "
".join(lines)


def main():
    parser = argparse.ArgumentParser(description="PR Review Agent")
    parser.add_argument("--pr", help="GitHub PR URL")
    parser.add_argument("--diff", help="Path to diff file")
    args = parser.parse_args()

    if args.pr:
        pr_info = fetch_pr_info(args.pr)
    elif args.diff:
        with open(args.diff) as f:
            diff = f.read()
        pr_info = {"diff": diff, "title": "Local diff", "author": "unknown",
                   "additions": 0, "deletions": 0, "files_changed": 0}
    else:
        print("Usage: review_agent.py --pr <PR_URL> or --diff <file>")
        sys.exit(1)

    findings = analyze_diff(pr_info)
    review = format_review(findings)
    print(review)

    # Save output
    with open("PR_REVIEW.md", "w") as f:
        f.write(review)


if __name__ == "__main__":
    main()
