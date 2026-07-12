#!/usr/bin/env python3
import argparse
import os
import sys
import json
try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    sys.exit(1)

try:
    from anthropic import Anthropic
except ImportError:
    print("Please install anthropic: pip install anthropic")
    sys.exit(1)

def get_pr_diff(pr_url, gh_token=None):
    # e.g., https://github.com/owner/repo/pull/123
    parts = pr_url.rstrip('/').split('/')
    if "pull" not in parts:
        print("Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123")
        sys.exit(1)
    
    idx = parts.index("pull")
    owner = parts[idx-2]
    repo = parts[idx-1]
    pull_number = parts[idx+1]
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"
        
    resp = requests.get(api_url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch PR diff: HTTP {resp.status_code}")
        print(resp.text)
        sys.exit(1)
        
    return resp.text

def main():
    parser = argparse.ArgumentParser(description="Claude PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--model", default="claude-3-7-sonnet-20250219", help="Anthropic model to use")
    
    args = parser.parse_args()
    
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)
        
    gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    
    print(f"Fetching diff for {args.pr}...", file=sys.stderr)
    diff_text = get_pr_diff(args.pr, gh_token)
    
    if not diff_text.strip():
        print("The PR diff is empty.", file=sys.stderr)
        sys.exit(1)
        
    client = Anthropic(api_key=anthropic_api_key)
    
    prompt = f"""You are an expert code reviewer. Analyze the following GitHub PR diff and provide a structured Markdown review.

Your output MUST be a valid Markdown document with the following sections EXACTLY as requested:
1. A summary of changes (2-3 sentences)
2. Identified risks (as a bulleted list)
3. Improvement suggestions (as a bulleted list)
4. Confidence score: Low / Medium / High (with a brief 1-sentence justification)

Here is the diff:
```diff
{diff_text}
```
"""
    print(f"Analyzing PR using {args.model}...", file=sys.stderr)
    try:
        message = client.messages.create(
            model=args.model,
            max_tokens=1500,
            temperature=0.0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        print("\n" + message.content[0].text)
    except Exception as e:
        print(f"Error calling Anthropic API: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
