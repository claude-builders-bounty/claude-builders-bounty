#!/usr/bin/env python3
import argparse
import subprocess
import requests
import json
import sys
import re
import os

def get_pr_diff(pr_url):
    """Fetch the raw diff from a GitHub PR URL"""
    # Extract owner, repo, and pull number from URL
    match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        print("Error: Invalid GitHub PR URL. Expected format: https://github.com/owner/repo/pull/123")
        sys.exit(1)
        
    owner, repo, pr_number = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    headers = {"Accept": "application/vnd.github.v3.diff"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
        
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching PR diff: {response.status_code} - {response.text}")
        sys.exit(1)
        
    return response.text, f"{owner}/{repo}#{pr_number}"

def review_with_claude(diff_text, pr_ref):
    """Use the local claude CLI to review the diff"""
    # Write diff to a temporary file
    with open(".temp_diff.patch", "w") as f:
        f.write(diff_text)
        
    prompt = f"""You are an expert Principal Software Engineer reviewing a Pull Request ({pr_ref}).

Read the diff from the `.temp_diff.patch` file and generate a structured Markdown review comment.
You MUST output EXACTLY this format, with these exact headers:

### Summary of Changes
(2-3 sentences summarizing what this PR actually does)

### Identified Risks
- (List any security, performance, or logic risks. If none, say "None identified")

### Improvement Suggestions
- (List actionable suggestions. If none, say "Looks good as is")

### Confidence Score
(Output exactly one of: Low / Medium / High)
"""
    
    print(f"Analyzing PR {pr_ref} with Claude Code...")
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    finally:
        if os.path.exists(".temp_diff.patch"):
            os.remove(".temp_diff.patch")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Claude Code PR Review Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    args = parser.parse_args()
    
    diff, pr_ref = get_pr_diff(args.pr)
    
    # Cap diff size if it's massive to avoid token limits
    if len(diff) > 50000:
        print("Warning: PR is very large. Truncating diff for analysis.")
        diff = diff[:50000] + "\n\n... [DIFF TRUNCATED] ..."
        
    review = review_with_claude(diff, pr_ref)
    
    print("\n" + "="*50 + "\n")
    print(review)
    print("\n" + "="*50 + "\n")
