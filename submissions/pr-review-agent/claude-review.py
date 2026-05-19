#!/usr/bin/env python3
"""
Claude Code PR Review Agent
Usage: python3 claude-review.py --pr https://github.com/owner/repo/pull/123
"""

import argparse
import os
import re
import sys
from urllib.parse import urlparse

import requests


def parse_pr_url(url: str) -> tuple:
    """Extract owner, repo, pr_number from GitHub PR URL."""
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not match:
        raise ValueError(f"Invalid PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the raw diff of a PR."""
    url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
    headers = {}
    
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'token {token}'
    
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def fetch_pr_info(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR metadata from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'token {token}'
    
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def analyze_with_claude(diff: str, pr_info: dict) -> str:
    """Call Claude API to analyze the PR diff."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable required")
    
    # Truncate diff if too large (Claude has context limits)
    max_diff_chars = 100000
    if len(diff) > max_diff_chars:
        diff = diff[:max_diff_chars] + "\n\n[... diff truncated due to length ...]"
    
    prompt = f"""You are a senior software engineer performing a code review.

PR Title: {pr_info.get('title', 'N/A')}
PR Description: {pr_info.get('body', 'No description provided.')[:2000]}
Author: {pr_info.get('user', {}).get('login', 'unknown')}
Files Changed: {pr_info.get('changed_files', '?')}
Additions: {pr_info.get('additions', '?')}, Deletions: {pr_info.get('deletions', '?')}

Here is the diff:

```diff
{diff}
```

Please provide a structured review in this exact format:

## Summary
2-3 sentences describing what this PR does and the overall approach.

## Identified Risks
- Risk 1: description
- Risk 2: description
(Include: logic errors, security issues, performance concerns, missing tests, breaking changes)

## Improvement Suggestions
- Suggestion 1: description
- Suggestion 2: description
(Include: code style, refactoring opportunities, better practices, test coverage)

## Confidence Score
**Low** | **Medium** | **High**

Choose based on:
- High: Clean, well-tested, follows conventions, no obvious issues
- Medium: Some concerns but generally sound, needs minor fixes
- Low: Significant issues, needs substantial revision before merge
"""

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"]


def main():
    parser = argparse.ArgumentParser(description="AI-powered PR review using Claude")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
        print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
        
        pr_info = fetch_pr_info(owner, repo, pr_number)
        diff = fetch_pr_diff(owner, repo, pr_number)
        
        print(f"📊 Analyzing {pr_info.get('changed_files', '?')} files ({len(diff)} chars diff)...", file=sys.stderr)
        
        review = analyze_with_claude(diff, pr_info)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(review)
            print(f"✅ Review saved to {args.output}", file=sys.stderr)
        else:
            print(review)
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
