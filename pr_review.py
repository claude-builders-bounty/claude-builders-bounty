#!/usr/bin/env python3
"""
PR Review Agent - Analyze GitHub PR diffs and generate structured Markdown reviews.
Usage: python pr_review.py --pr https://github.com/owner/repo/pull/123
"""

import sys
import os
import re
import argparse
import subprocess
import json
from datetime import datetime


def get_gh_auth():
    """Get GitHub token from gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token", "--hostname", "github.com"],
            capture_output=True, text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN", "")


def fetch_pr_diff(owner, repo, pr_number, token):
    """Fetch PR diff via GitHub API."""
    import urllib.request
    import urllib.error

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff"
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error fetching PR: {e}")
        return None


def fetch_pr_details(owner, repo, pr_number, token):
    """Fetch PR metadata."""
    import urllib.request

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return {}


def analyze_risks(diff):
    """Analyze diff for common risks."""
    risks = []

    # Check for security issues
    if re.search(r'password\s*=\s*["\'][^"\']+["\']', diff, re.IGNORECASE):
        risks.append("Hardcoded credentials detected - use environment variables")
    if re.search(r'api[_-]?key\s*=\s*["\'][^"\']+["\']', diff, re.IGNORECASE):
        risks.append("API key hardcoded - use secrets management")
    if re.search(r'SQL\s|SELECT\s|INSERT\s|UPDATE\s|DELETE\s', diff, re.IGNORECASE):
        risks.append("Raw SQL detected - ensure parameterized queries to prevent injection")
    if re.search(r'exec\s*\(|eval\s*\(', diff):
        risks.append("Dynamic code execution (exec/eval) - potential security risk")
    if re.search(r'console\.log\(|print\s*\(', diff):
        risks.append("Debug logging in code - remove before production")
    if re.search(r'@app\.route.*methods.*GET.*POST', diff) and not re.search(r'@app\.route.*methods.*POST.*GET', diff):
        risks.append("CSRF vulnerability - ensure proper protection on state-changing routes")

    # Check for breaking changes
    if re.search(r'class\s+\w+.*\(.*object.*\):', diff):
        risks.append("Legacy class definition - consider modern Python patterns")
    if re.search(r'return\s+None|->\s*None', diff) and re.search(r'\.delete\(|\.drop\(', diff):
        risks.append("Deletion operation detected - verify cascade behavior")

    return risks


def analyze_suggestions(diff):
    """Analyze diff and suggest improvements."""
    suggestions = []

    if not re.search(r'type\s+\w+\s*[:=]', diff) and not re.search(r'interface\s+\w+', diff):
        if re.search(r'\w+\s*=\s*\{', diff):
            suggestions.append("Consider adding TypeScript types for better type safety")
    if re.search(r'#.*TODO|#.*FIXME|#.*XXX', diff):
        suggestions.append("TODO/FIXME comments found - ensure they are tracked in issues")
    if re.search(r'try:[\s\S]{0,50}except[\s\S]{0,50}pass', diff):
        suggestions.append("Empty except blocks detected - handle errors properly")
    if re.search(r'\.forEach\(', diff):
        suggestions.append("Consider using async/await with map instead of forEach for better control flow")
    if not re.search(r'test', diff, re.IGNORECASE) and not re.search(r'__test__|\.test\.|\.spec\.', diff):
        suggestions.append("No test files detected - consider adding tests for new functionality")

    return suggestions


def generate_review(diff, pr_details):
    """Generate structured Markdown review."""
    title = pr_details.get("title", "Untitled PR")
    body = pr_details.get("body", "")
    additions = pr_details.get("additions", 0)
    deletions = pr_details.get("deletions", 0)
    changed_files = pr_details.get("changed_files", 0)

    risks = analyze_risks(diff)
    suggestions = analyze_suggestions(diff)

    # Calculate confidence based on diff size and complexity
    lines = len(diff.splitlines())
    if lines < 50:
        confidence = "High"
    elif lines < 300:
        confidence = "Medium"
    else:
        confidence = "Low"

    review = f"""# PR Review

## Summary

"""
    if title:
        review += f"**{title}**\n\n"
    review += f"Changes across {changed_files} files with {additions} additions and {deletions} deletions. "

    if risks:
        review += "This PR introduces some areas requiring attention."
    elif suggestions:
        review += "This PR is clean with minor improvement opportunities."
    else:
        review += "This PR looks well-structured with no major concerns."

    review += "\n\n"

    if risks:
        review += "## Identified Risks\n\n"
        for risk in risks:
            review += f"- {risk}\n"
        review += "\n"

    if suggestions:
        review += "## Improvement Suggestions\n\n"
        for suggestion in suggestions:
            review += f"- {suggestion}\n"
        review += "\n"

    review += f"## Confidence Score\n\n**{confidence}**\n\n"
    review += f"---\n*Review generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by PR Review Agent*\n"

    return review


def main():
    parser = argparse.ArgumentParser(description="PR Review Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    # Parse PR URL
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', args.pr)
    if not match:
        print("Invalid PR URL format")
        sys.exit(1)

    owner, repo, pr_number = match.groups()
    token = get_gh_auth()

    print(f"Fetching PR #{pr_number} from {owner}/{repo}...")

    diff = fetch_pr_diff(owner, repo, pr_number, token)
    pr_details = fetch_pr_details(owner, repo, pr_number, token)

    if not diff:
        print("Failed to fetch PR diff")
        sys.exit(1)

    review = generate_review(diff, pr_details)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review)
        print(f"Review written to {args.output}")
    else:
        print(review)


if __name__ == "__main__":
    main()
