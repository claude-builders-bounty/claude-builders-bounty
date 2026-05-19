#!/usr/bin/env python3
import os
import sys
import argparse
import requests
import json
from urllib.parse import urlparse

def fetch_pr_diff(pr_url):
    # Convert github.com PR URL to API URL to get diff
    # Format: https://github.com/owner/repo/pull/123
    parsed = urlparse(pr_url)
    parts = parsed.path.strip('/').split('/')
    if len(parts) < 4 or parts[2] != 'pull':
        print("Error: Invalid GitHub PR URL format.", file=sys.stderr)
        sys.exit(1)
        
    owner, repo, _, pr_number = parts[:4]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    headers = {"Accept": "application/vnd.github.v3.diff"}
    # Use GITHUB_TOKEN if available to avoid rate limits
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.environ.get('GITHUB_TOKEN')}"
        
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching PR diff: {response.status_code} {response.text}", file=sys.stderr)
        sys.exit(1)
        
    return response.text

def generate_review(diff):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)
        
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    prompt = f"""You are an expert code reviewer. Please analyze the following Git diff and provide a structured review in Markdown format.

Your review must contain EXACTLY these four sections:
1. **Summary of changes**: 2-3 sentences explaining what this PR does.
2. **Identified risks**: A bulleted list of potential bugs, security issues, or performance regressions.
3. **Improvement suggestions**: A bulleted list of actionable improvements to the code.
4. **Confidence score**: "Low", "Medium", or "High" (just the word, based on your confidence in the review).

Here is the diff:
```diff
{diff}
```
"""

    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Error calling Anthropic API: {response.status_code} {response.text}", file=sys.stderr)
        sys.exit(1)
        
    data = response.json()
    return data['content'][0]['text']

def main():
    parser = argparse.ArgumentParser(description="Claude PR Review Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    args = parser.parse_args()
    
    print(f"Fetching diff for {args.pr}...", file=sys.stderr)
    diff = fetch_pr_diff(args.pr)
    
    # Truncate diff if it's too large to prevent blowing up the context window
    if len(diff) > 50000:
        diff = diff[:50000] + "\n... [Diff truncated due to size]"
        
    print("Generating review via Claude API...", file=sys.stderr)
    review = generate_review(diff)
    
    print("\n" + "="*50 + "\n")
    print(review)
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
