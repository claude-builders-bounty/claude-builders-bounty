#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent

CLI tool that reviews a GitHub PR and generates a structured Markdown review.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr 123 --repo owner/repo --token YOUR_TOKEN
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime

def get_pr_diff(repo: str, pr_number: int, token: str) -> dict:
    """Fetch PR details and diff from GitHub API"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff"
    }

    # Get PR info
    pr_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(pr_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            pr_data = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"Failed to fetch PR: {e.code} {e.reason}"}

    # Get diff
    diff_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(diff_url, headers={
        **headers,
        "Accept": "application/vnd.github.v3.diff"
    })
    try:
        with urllib.request.urlopen(req) as response:
            diff = response.read().decode()
    except urllib.error.HTTPError:
        diff = ""

    return {
        "title": pr_data.get("title", ""),
        "body": pr_data.get("body", ""),
        "state": pr_data.get("state", ""),
        "author": pr_data.get("user", {}).get("login", ""),
        "head": pr_data.get("head", {}).get("ref", ""),
        "base": pr_data.get("base", {}).get("ref", ""),
        "changed_files": pr_data.get("changed_files", 0),
        "additions": pr_data.get("additions", 0),
        "deletions": pr_data.get("deletions", 0),
        "diff": diff[:15000]  # Limit diff size
    }

def analyze_pr_with_claude(pr_data: dict, claude_api_key: str) -> dict:
    """Send PR data to Claude API for analysis"""
    prompt = f"""You are a code reviewer. Analyze this GitHub Pull Request and provide a structured review.

## PR Information
- Title: {pr_data.get('title', 'N/A')}
- Author: {pr_data.get('author', 'N/A')}
- Branch: {pr_data.get('head', 'N/A')} → {pr_data.get('base', 'N/A')}
- Files changed: {pr_data.get('changed_files', 0)}
- Additions: {pr_data.get('additions', 0)}
- Deletions: {pr_data.get('deletions', 0)}

## PR Description
{pr_data.get('body', 'No description provided.')}

## Diff (first 15000 chars)
{pr_data.get('diff', 'No diff available.')}

## Output Format
Provide a Markdown review with these sections:

### Summary
2-3 sentences describing what this PR does.

### Identified Risks
List potential risks or concerns (or "No significant risks identified" if none).

### Improvement Suggestions
List actionable suggestions for improving the code (or "No suggestions" if none).

### Confidence Score
Low / Medium / High - based on how confident you are in this review.
"""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": claude_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return {"review": result["content"][0]["text"]}
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read().decode()) if e.read else {}
        return {"error": f"Claude API error: {e.code} - {error_body.get('error', {}).get('message', str(e))}"}

def generate_local_review(pr_data: dict) -> str:
    """Generate a basic review without Claude API"""
    summary = f"This PR '{pr_data.get('title', 'N/A')}' by {pr_data.get('author', 'unknown')} "
    summary += f"modifies {pr_data.get('changed_files', 0)} files with "
    summary += f"{pr_data.get('additions', 0)} additions and {pr_data.get('deletions', 0)} deletions."

    risks = []
    diff = pr_data.get('diff', '')

    # Basic risk detection
    if 'DROP TABLE' in diff.upper():
        risks.append("SQL DROP TABLE detected - ensure proper backups exist")
    if 'rm -rf' in diff:
        risks.append("Recursive delete command detected - verify target is correct")
    if 'password' in diff.lower() or 'secret' in diff.lower() or 'api_key' in diff.lower():
        risks.append("Potential credential exposure - ensure secrets are not committed")
    if 'eval(' in diff:
        risks.append("eval() usage detected - potential code injection risk")

    if not risks:
        risks = ["No significant risks identified"]

    suggestions = [
        "Ensure tests cover the changes",
        "Check that error handling is appropriate",
        "Verify documentation is updated if needed"
    ]

    # Estimate confidence
    lines = len(diff.split('\n'))
    if lines < 50:
        confidence = "High"
    elif lines < 200:
        confidence = "Medium"
    else:
        confidence = "Low"

    return f"""## Summary
{summary}

## Identified Risks
{chr(10).join(f"- {r}" for r in risks)}

## Improvement Suggestions
{chr(10).join(f"- {s}" for s in suggestions)}

## Confidence Score
{confidence}

---
*Review generated locally. Set ANTHROPIC_API_KEY for AI-powered analysis.*
"""

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="PR URL or PR number")
    parser.add_argument("--repo", help="Repository in format 'owner/repo' (required if --pr is a number)")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token")
    parser.add_argument("--claude-key", default=os.environ.get("ANTHROPIC_API_KEY"), help="Anthropic API key for Claude")
    args = parser.parse_args()

    # Parse PR number and repo
    pr_number_match = re.search(r'/pull/(\d+)', str(args.pr))
    if pr_number_match:
        pr_number = int(pr_number_match.group(1))
        repo_match = re.search(r'github\.com/([^/]+/[^/]+)', str(args.pr))
        repo = repo_match.group(1) if repo_match else args.repo
    else:
        pr_number = int(args.pr)
        repo = args.repo

    if not repo:
        print("Error: --repo is required when --pr is a number")
        sys.exit(1)

    token = args.token or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Error: GitHub token required (--token or GITHUB_TOKEN env var)")
        sys.exit(1)

    print(f"Fetching PR {pr_number} from {repo}...", file=sys.stderr)
    pr_data = get_pr_diff(repo, pr_number, token)

    if "error" in pr_data:
        print(f"Error: {pr_data['error']}")
        sys.exit(1)

    print("Generating review...", file=sys.stderr)

    if args.claude_key:
        result = analyze_pr_with_claude(pr_data, args.claude_key)
        if "error" in result:
            print(f"Claude API error: {result['error']}, falling back to local review", file=sys.stderr)
            review = generate_local_review(pr_data)
        else:
            review = result["review"]
    else:
        review = generate_local_review(pr_data)

    print(review)

if __name__ == "__main__":
    main()