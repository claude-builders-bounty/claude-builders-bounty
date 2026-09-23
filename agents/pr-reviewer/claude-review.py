#!/usr/bin/env python3
import argparse
import urllib.request
import json
import os
import sys

def get_pr_diff(pr_url):
    diff_url = pr_url.rstrip('/') + '.diff'
    req = urllib.request.Request(diff_url)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching PR diff: {e}")
        sys.exit(1)

def call_claude(diff):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.")
        sys.exit(1)
        
    prompt = f"""You are an expert code reviewer. Analyze the following GitHub Pull Request diff and provide a structured Markdown review.

Required format exactly as follows:
### 📝 Summary of Changes
(2-3 sentences summarizing the diff)

### ⚠️ Identified Risks
- (List any security, performance, or logic risks. If none, state "None identified".)

### 💡 Improvement Suggestions
- (List suggestions for better code quality, readability, or best practices.)

### 📊 Confidence Score
(Low / Medium / High)

Here is the PR diff:
--- DIFF START ---
{diff}
--- DIFF END ---
"""
    
    data = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "system": "You are an expert PR reviewer. Always strictly follow the requested Markdown structure.",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(data).encode('utf-8'),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['content'][0]['text']
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Claude PR Review Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    args = parser.parse_args()
    
    print(f"Fetching diff for {args.pr}...")
    diff = get_pr_diff(args.pr)
    
    if len(diff.strip()) == 0:
        print("Error: PR diff is empty or invalid.")
        sys.exit(1)
        
    print("Analyzing with Claude...\\n")
    print("-" * 40)
    review = call_claude(diff)
    print(review)
    print("-" * 40)

if __name__ == "__main__":
    main()
