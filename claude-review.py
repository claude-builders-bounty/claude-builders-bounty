#!/usr/bin/env python3
import argparse
import urllib.request
import json
import os
import sys

def get_pr_diff(pr_url):
    parts = pr_url.rstrip('/').split('/')
    owner, repo, pull_number = parts[-4], parts[-3], parts[-1]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    
    req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github.v3.diff"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"token {os.environ['GITHUB_TOKEN']}")
        
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching PR diff: {e}")
        sys.exit(1)

def call_claude(diff_text):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is missing.")
        sys.exit(1)
        
    prompt = f"""Please analyze this git diff and provide a structured review in Markdown.
    
    Format exactly like this:
    ### Summary of changes
    (Provide 2-3 sentences summarizing the diff)
    
    ### Identified risks
    - (list any bugs, security issues, or performance risks)
    
    ### Improvement suggestions
    - (list specific code improvements)
    
    ### Confidence score
    (Low, Medium, or High)
    
    Diff:
    {diff_text}
    """
    
    data = {
        "model": "claude-3-5-sonnet-20240620",
        "max_tokens": 1024,
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Claude Code PR Review Sub-agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    args = parser.parse_args()
    
    diff = get_pr_diff(args.pr)
    if not diff.strip():
        print("PR has no changes or could not fetch diff.")
        sys.exit(0)
        
    review = call_claude(diff[:50000]) # truncated for API limits
    print(review)
