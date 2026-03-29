#!/usr/bin/env python3
"""
claude-review — CLI PR reviewer via Claude API
Bounty #210 - $150

Usage:
    claude_review.py --pr-url <PR_URL> --anthropic-key <KEY>
    claude_review.py --repo <OWNER/REPO> --pr-number <N> --anthropic-key <KEY>
"""

import argparse
import json
import os
import sys
import requests
from typing import Optional, Dict, Any

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

def fetch_pr_details(owner: str, repo: str, pr_number: int, github_token: str) -> Dict[str, Any]:
    """Fetch PR details from GitHub API."""
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get PR info
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    pr_response = requests.get(pr_url, headers=headers)
    pr_response.raise_for_status()
    pr_data = pr_response.json()
    
    # Get PR diff
    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}.diff"
    diff_response = requests.get(diff_url, headers=headers)
    diff_response.raise_for_status()
    diff_content = diff_response.text
    
    # Get comments
    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    comments_response = requests.get(comments_url, headers=headers)
    comments = comments_response.json() if comments_response.ok else []
    
    return {
        "pr": pr_data,
        "diff": diff_content,
        "comments": comments
    }

def generate_review(pr_data: Dict, diff: str, comments: list, anthropic_key: str) -> str:
    """Generate PR review using Claude API."""
    headers = {
        "x-api-key": anthropic_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    prompt = f"""You are an expert code reviewer. Review this pull request and provide a structured, helpful review.

## PR Information
- **Title**: {pr_data.get('title', 'N/A')}
- **Author**: {pr_data.get('user', {}).get('login', 'N/A')}
- **Description**: {pr_data.get('body', 'No description provided')[:2000]}

## Code Changes
```diff
{diff[:15000]}
```

## Existing Comments
{json.dumps(comments[:10], indent=2)[:2000] if comments else "No comments yet"}

---

Please provide a structured review with:

1. **Summary** - Brief overview of changes
2. **Strengths** - What's done well
3. **Concerns** - Issues, bugs, or improvements needed
4. **Suggestions** - Specific actionable recommendations
5. **Verdict** - APPROVE, REQUEST_CHANGES, or COMMENT

Be constructive, specific, and kind. Focus on code quality, security, performance, and maintainability."""

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2048,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    
    return result["content"][0]["text"]

def post_review(owner: str, repo: str, pr_number: int, review: str, github_token: str):
    """Post review as a comment on the PR."""
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    payload = {"body": f"## 🤖 Automated PR Review\n\n{review}"}
    
    response = requests.post(comment_url, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()

def main():
    parser = argparse.ArgumentParser(description="Claude-powered PR reviewer")
    parser.add_argument("--pr-url", help="Full PR URL")
    parser.add_argument("--repo", help="Repository (owner/repo)")
    parser.add_argument("--pr-number", type=int, help="PR number")
    parser.add_argument("--anthropic-key", help="Anthropic API key (or set ANTHROPIC_API_KEY)")
    parser.add_argument("--github-token", help="GitHub token (or set GITHUB_TOKEN)")
    parser.add_argument("--post", action="store_true", help="Post review as comment")
    parser.add_argument("--output", help="Output file for review")
    
    args = parser.parse_args()
    
    # Parse PR URL if provided
    if args.pr_url:
        # Parse URL: https://github.com/owner/repo/pull/123
        parts = args.pr_url.rstrip("/").split("/")
        if len(parts) >= 7 and "pull" in parts:
            args.repo = f"{parts[3]}/{parts[4]}"
            args.pr_number = int(parts[6])
    
    if not args.repo or not args.pr_number:
        parser.error("--pr-url or (--repo and --pr-number) is required")
    
    # Get API keys
    anthropic_key = args.anthropic_key or os.environ.get("ANTHROPIC_API_KEY")
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    
    if not anthropic_key:
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    
    if args.post and not github_token:
        print("Error: GITHUB_TOKEN required for --post", file=sys.stderr)
        sys.exit(1)
    
    # Parse repo
    owner, repo = args.repo.split("/")
    
    print(f"🔍 Fetching PR #{args.pr_number} from {owner}/{repo}...")
    pr_data = fetch_pr_details(owner, repo, args.pr_number, github_token or "")
    
    print(f"📝 Generating review with Claude...")
    review = generate_review(pr_data["pr"], pr_data["diff"], pr_data["comments"], anthropic_key)
    
    # Output review
    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"✅ Review saved to {args.output}")
    else:
        print("\n" + "="*60)
        print(review)
        print("="*60)
    
    # Post review if requested
    if args.post and github_token:
        print(f"📤 Posting review to PR...")
        result = post_review(owner, repo, args.pr_number, review, github_token)
        print(f"✅ Review posted: {result['html_url']}")
    
    print("\n✅ Review complete!")

if __name__ == "__main__":
    main()
