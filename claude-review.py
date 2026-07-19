#!/usr/bin/env python3
import sys
import os
import requests
import json
import argparse

def get_pr_diff(pr_url):
    # Convert https://github.com/owner/repo/pull/123 to API URL
    pr_url = pr_url.rstrip("/")
    parts = pr_url.replace("https://github.com/", "").split("/")
    if len(parts) < 4:
        raise ValueError("Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123")
    
    owner, repo, pr_num = parts[0], parts[1], parts[3]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    
    headers = {"Accept": "application/vnd.github.v3.diff"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
        
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    return response.text

def review_diff(diff):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)
        
    prompt = f"""You are an expert code reviewer. Please review the following Pull Request diff.
Return a structured Markdown response exactly as follows:

### Summary of Changes
[2-3 sentences summarizing the diff]

### Identified Risks
- [Risk 1]
- [Risk 2]
(If none, explicitly state "None identified")

### Improvement Suggestions
- [Suggestion 1]
- [Suggestion 2]
(If none, explicitly state "Looks good as is")

### Confidence Score
[Low / Medium / High]

Here is the diff:
{diff}
"""

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    response.raise_for_status()
    
    return response.json()["content"][0]["text"]

def main():
    parser = argparse.ArgumentParser(description="Claude PR Review Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    args = parser.parse_args()
    
    try:
        diff = get_pr_diff(args.pr)
        review = review_diff(diff)
        print(review)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
