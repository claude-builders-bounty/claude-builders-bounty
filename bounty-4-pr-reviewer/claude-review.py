#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import json
import urllib.request

def get_pr_diff(pr_url):
    try:
        # Fetch diff using GitHub CLI
        result = subprocess.run(["gh", "pr", "diff", pr_url], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR diff: {e.stderr}", file=sys.stderr)
        print("Make sure you have `gh` CLI installed and authenticated.", file=sys.stderr)
        sys.exit(1)

def call_anthropic_api(diff_text):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is missing.", file=sys.stderr)
        sys.exit(1)
        
    prompt = f"""You are an expert code reviewer analyzing a pull request.
Review the following code diff and return a structured Markdown comment.
Your output must strictly follow these exact headings:

## Summary of changes
[2-3 sentences summarizing what changed]

## Identified risks
- [Risk 1]
- [Risk 2]
- (If none, state "No major risks identified")

## Improvement suggestions
- [Suggestion 1]
- [Suggestion 2]
- (If none, state "Looks solid, no further improvements needed")

## Confidence score
[Low / Medium / High]

Code diff to analyze:
```diff
{diff_text}
```"""

    data = json.dumps({
        "model": "claude-3-7-sonnet-20250219",
        "max_tokens": 2048,
        "temperature": 0.2,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            return res_body["content"][0]["text"]
    except urllib.error.HTTPError as e:
        print(f"API Error: {e.read().decode('utf-8')}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Claude PR Reviewer")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    args = parser.parse_args()
    
    print(f"Fetching diff for {args.pr}...", file=sys.stderr)
    diff = get_pr_diff(args.pr)
    
    if not diff.strip():
        print("No diff found or PR is empty.", file=sys.stderr)
        sys.exit(0)
        
    print(f"Diff fetched ({len(diff)} characters). Analyzing with Claude...", file=sys.stderr)
    review = call_anthropic_api(diff)
    
    print("\n--- Review Output ---\n", file=sys.stderr)
    print(review)

if __name__ == "__main__":
    main()
