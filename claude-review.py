#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent
Usage: python3 claude-review.py --pr https://github.com/owner/repo/pull/123
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Optional


def run_command(cmd: str) -> str:
    """Run shell command and return output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


def parse_pr_url(url: str) -> tuple[str, str]:
    """Parse GitHub PR URL to repo and PR number."""
    parts = url.replace("https://github.com/", "").split("/")
    if len(parts) < 3:
        raise ValueError(f"Invalid PR URL: {url}")
    return f"{parts[0]}/{parts[1]}", parts[2]


def get_pr_diff(repo: str, pr_num: str) -> str:
    """Get PR diff."""
    return run_command(f"gh pr diff {pr_num} --repo {repo}")


def get_pr_info(repo: str, pr_num: str) -> dict:
    """Get PR metadata."""
    result = run_command(
        f"gh pr view {pr_num} --repo {repo} --json title,body,author,files "
        f"--jq '{{title: .title, body: .body[:500], author: .author.login, files: .files | length}}'"
    )
    return json.loads(result)


def analyze_diff(diff: str) -> dict:
    """Analyze diff for risks and patterns."""
    lines = diff.split("\n")
    added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))

    risks = []
    if "password" in diff.lower() or "secret" in diff.lower() or "api_key" in diff.lower():
        risks.append("Possible hardcoded secrets or credentials detected")
    if "eval(" in diff or "exec(" in diff:
        risks.append("Dynamic code execution detected - review for injection risks")
    if "TODO" in diff or "FIXME" in diff:
        risks.append("Incomplete implementation detected")
    if removed > added * 2:
        risks.append("Large number of deletions - verify no functionality loss")

    return {
        "lines_added": added,
        "lines_removed": removed,
        "risks": risks if risks else ["No critical risks identified"],
        "has_tests": "test" in diff.lower() or "spec" in diff.lower(),
    }


def generate_review(pr_info: dict, diff: str, analysis: dict) -> str:
    """Generate structured review comment."""
    files_changed = pr_info.get("files", 0)

    review = f"""# PR Review: {pr_info['title']}

**Author:** @{pr_info['author']}
**Files changed:** {files_changed}
**Lines:** +{analysis['lines_added']} / -{analysis['lines_removed']}

## Summary
This PR modifies {analysis['lines_added']} lines across {files_changed} files.

## Risks
"""
    for risk in analysis["risks"]:
        review += f"- {risk}\n"

    review += "\n## Improvements\n"
    if not analysis["has_tests"]:
        review += "- ⚠️ No test files detected - consider adding unit tests\n"
    review += "- Verify backward compatibility\n"
    review += "- Add inline comments for complex logic\n"

    # Confidence score
    confidence = "High" if analysis["lines_added"] < 100 and not analysis["risks"] else "Medium"
    if analysis["lines_added"] > 500 or len(analysis["risks"]) > 2:
        confidence = "Low"

    review += f"\n## Confidence: {confidence}\n"

    return review


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    args = parser.parse_args()

    try:
        repo, pr_num = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get PR data
    pr_info = get_pr_info(repo, pr_num)
    diff = get_pr_diff(repo, pr_num)

    if not diff:
        print("Warning: Could not fetch PR diff", file=sys.stderr)

    # Analyze and generate review
    analysis = analyze_diff(diff)
    review = generate_review(pr_info, diff, analysis)

    print(review)


if __name__ == "__main__":
    main()
