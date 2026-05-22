#!/usr/bin/env python3

import os
import sys
import json
import requests
import argparse
import subprocess
from github import Github

def get_pr_diff(repo_owner, repo_name, pr_number, github_token=None):
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if github_token:
        headers["Authorization"] = f"token {github_token}"
        
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching diff: {response.status_code} - {response.text}")
        sys.exit(1)
        
    return response.text

def analyze_diff_with_claude(diff, api_key, model="claude-3-5-sonnet-20241022"):
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    system_prompt = """You are an expert code reviewer. Analyze the provided git diff and create a structured Markdown review comment.
    
Your output MUST follow this exact structure:
### 📝 Summary of Changes
(2-3 sentences explaining what this PR does)

### ⚠️ Identified Risks
- (List any security, performance, or logic risks. If none, state "No major risks identified.")

### 💡 Improvement Suggestions
- (List actionable suggestions. If perfect, state "Code looks solid.")

### 📊 Confidence Score
**Confidence:** (High / Medium / Low)"""

    data = {
        "model": model,
        "max_tokens": 1500,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": f"Please review this diff:\n\n```diff\n{diff[:50000]}\n```" # Cap at 50k chars to avoid token limits
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        print(f"Error calling Claude: {response.status_code} - {response.text}")
        sys.exit(1)
        
    return response.json()["content"][0]["text"]

def parse_pr_url(url):
    # e.g. https://github.com/owner/repo/pull/123
    parts = url.rstrip('/').split('/')
    if "github.com" not in parts or "pull" not in parts:
        raise ValueError("Invalid GitHub PR URL")
        
    pr_number = parts[-1]
    repo_name = parts[-3]
    owner = parts[-4]
    
    return owner, repo_name, pr_number

def post_comment(owner, repo, pr_number, comment, github_token):
    if not github_token:
        print("GITHUB_TOKEN not provided, outputting to console instead:")
        print(comment)
        return
        
    g = Github(github_token)
    repo = g.get_repo(f"{owner}/{repo}")
    pr = repo.get_pull(int(pr_number))
    pr.create_issue_comment(comment)
    print(f"Successfully posted comment to PR #{pr_number}")

def main():
    parser = argparse.ArgumentParser(description="Claude PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--api-key", help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var)")
    parser.add_argument("--github-token", help="GitHub token for fetching diffs and posting comments (defaults to GITHUB_TOKEN env var)")
    parser.add_argument("--post", action="store_true", help="Post the review as a comment on the PR (requires github token)")
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Anthropic API key is required. Pass --api-key or set ANTHROPIC_API_KEY env var.")
        sys.exit(1)
        
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    
    try:
        owner, repo_name, pr_number = parse_pr_url(args.pr)
        print(f"Fetching diff for {owner}/{repo_name}#{pr_number}...")
        diff = get_pr_diff(owner, repo_name, pr_number, github_token)
        
        print("Analyzing with Claude...")
        review = analyze_diff_with_claude(diff, api_key)
        
        print("\n--- Review Output ---\n")
        print(review)
        print("\n---------------------\n")
        
        if args.post:
            if not github_token:
                print("Error: --post requires a GitHub token.")
                sys.exit(1)
            print("Posting comment to GitHub...")
            post_comment(owner, repo_name, pr_number, review, github_token)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
