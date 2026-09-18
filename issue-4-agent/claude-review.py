#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import requests

def get_pr_diff(pr_url):
    # E.g., https://github.com/owner/repo/pull/123
    diff_url = pr_url.rstrip('/') + '.diff'
    response = requests.get(diff_url)
    if response.status_code != 200:
        print(f"Failed to fetch diff: {response.status_code}")
        sys.exit(1)
    return response.text

def review_diff(diff_content, api_key):
    # This acts as the sub-agent calling Claude API directly
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    prompt = f"""You are a senior code reviewer. Please review the following PR diff.
Return your answer exactly in this Markdown structure:

### Summary of Changes
(2-3 sentences summarizing the PR)

### Identified Risks
- (List any security, performance, or logic risks. If none, write 'None identified.')

### Improvement Suggestions
- (List any code quality, style, or architectural suggestions. If none, write 'No improvements needed.')

### Confidence Score
(Low / Medium / High)

Diff:
```diff
{diff_content}
```
"""

    payload = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['content'][0]['text']
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        if response and response.text:
            print(f"Response data: {response.text}")
        sys.exit(1)

def post_comment(pr_url, comment):
    # We use gh CLI to post the comment back to the PR
    # E.g., gh pr comment https://github.com/owner/repo/pull/123 --body "comment"
    try:
        subprocess.run(
            ['gh', 'pr', 'comment', pr_url, '--body', comment],
            check=True
        )
        print("Successfully posted the review comment to the PR!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to post comment via gh CLI: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Sub-Agent")
    parser.add_argument('--pr', required=True, help='Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)')
    parser.add_argument('--post', action='store_true', help='If set, uses gh CLI to post the review as a PR comment')
    
    args = parser.parse_args()
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is missing.")
        sys.exit(1)
        
    print(f"Fetching diff for {args.pr}...")
    diff_content = get_pr_diff(args.pr)
    
    # Optional truncation for massive PRs
    if len(diff_content) > 100000:
        print("Diff is extremely large, truncating to 100k characters...")
        diff_content = diff_content[:100000]
        
    print("Sending diff to Claude API for analysis...")
    review = review_diff(diff_content, api_key)
    
    print("\n--- Review Output ---\n")
    print(review)
    print("\n---------------------\n")
    
    if args.post:
        print("Posting to GitHub...")
        post_comment(args.pr, review)

if __name__ == '__main__':
    main()
