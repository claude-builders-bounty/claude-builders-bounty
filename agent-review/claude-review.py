#!/usr/bin/env python3
import sys
import argparse
import requests
import os
import json

try:
    from anthropic import Anthropic
except ImportError:
    print("Please install the anthropic package: pip install anthropic")
    sys.exit(1)

def get_pr_diff(pr_url: str) -> str:
    # Ensure URL ends with .diff
    if not pr_url.endswith(".diff"):
        if pr_url.endswith("/"):
            pr_url = pr_url[:-1]
        diff_url = pr_url + ".diff"
    else:
        diff_url = pr_url
        
    response = requests.get(diff_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR diff: HTTP {response.status_code}")
    return response.text

def review_diff(diff: str, api_key: str) -> str:
    client = Anthropic(api_key=api_key)
    
    prompt = f"""You are an expert software engineer performing a code review.
Please review the following git diff and provide a structured Markdown response with the following sections:
1. **Summary of changes**: A brief 2-3 sentence summary.
2. **Identified risks**: A bulleted list of potential bugs, security issues, or performance risks.
3. **Improvement suggestions**: A bulleted list of actionable suggestions for cleaner, better code.
4. **Confidence score**: Simply state Low, Medium, or High.

Here is the diff:
```diff
{diff}
```
"""
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=2048,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text

def main():
    parser = argparse.ArgumentParser(description="Claude PR Review Agent")
    parser.add_argument("--pr", required=True, help="URL to the GitHub Pull Request")
    args = parser.parse_args()
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.")
        sys.exit(1)
        
    try:
        print(f"Fetching diff for {args.pr}...", file=sys.stderr)
        diff = get_pr_diff(args.pr)
        if not diff.strip():
            print("The PR diff is empty. Nothing to review.")
            return
            
        print("Analyzing with Claude...", file=sys.stderr)
        review = review_diff(diff, api_key)
        
        print("\n" + review + "\n")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
