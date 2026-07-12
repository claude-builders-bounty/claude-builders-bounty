#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent
Reviews a PR and generates structured Markdown comments.
"""

import argparse
import os
import sys
import requests
import json
import re
from typing import List, Dict
import openai
from urllib.parse import urlparse, parse_qs
import subprocess

# Default to a reasonable model
DEFAULT_MODEL = "gpt-3.5-turbo"

def get_pr_diff(repo_owner: str, repo_name: str, pr_number: int, github_token: str) -> str:
    """Fetch PR diff using GitHub API"""
    headers = {
        "Authorization": f"Bearer {github_token}" if github_token else None,
        "Accept": "application/vnd.github.v3+json"
    }
    
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    response = requests.get(api_url, headers={k: v for k, v in headers.items() if v is not None})
    response.raise_for_status()
    
    data = response.json()
    if 'diff_url' in data:
        diff_response = requests.get(data['diff_url'], headers={k: v for k, v in headers.items() if v is not None})
        diff_response.raise_for_status()
        return diff_response.text
    elif 'patch' in data:
        return data['patch']
    else:
        # Fallback to manually fetching the diff
        diff_url = data.get('diff_url')
        if diff_url:
            diff_response = requests.get(diff_url, headers={k: v for k, v in headers.items() if v is not None})
            diff_response.raise_for_status()
            return diff_response.text
    return ""

def analyze_code_with_claude(diff_content: str, model: str = DEFAULT_MODEL) -> str:
    """
    Send diff to Claude and get analysis
    """
    # In a real implementation, you would use the Claude API
    # For this implementation, we'll simulate the API call
    # and return a mock structured review
    
    # This is where you would integrate with Claude API in a real implementation
    # For now, we'll return a mock response
    return """## Summary of Changes

This pull request modifies the main application file to update the greeting message and adds a new feature for user authentication. The changes include a new login endpoint and modifications to the session management system.

## Identified Risks

- The new authentication logic may introduce security vulnerabilities if not properly implemented
- Session management changes could potentially cause issues with concurrent user access
- The database schema changes might not be backward compatible

## Improvement Suggestions

- Add input validation for the new login endpoint parameters
- Review the session timeout implementation for security best practices
- Add unit tests for the new authentication logic
- Consider adding rate limiting to the new login endpoint

## Confidence: High
"""

def parse_github_url(pr_url: str) -> tuple:
    """Parse GitHub URL to extract owner, repo, and PR number"""
    # Handle both HTTPS and SSH URLs
    if pr_url.startswith("https://github.com/"):
        # HTTPS format: https://github.com/owner/repo/pull/123
        pattern = r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.match(pattern, pr_url)
        if match:
            owner, repo, pr_number = match.groups()
            return owner, repo, int(pr_unit)
    elif pr_url.startswith("git@github.com:"):
        # SSH format: git@github.com:owner/repo.git
        pattern = r"git@github.com:([^/]+)/([^/]+)\.git"
        match = re.search(pattern, pr_url)
        if match:
            owner, repo = match.groups()
            # Extract PR number from branch name or other means if available
            pr_number = 0  # Default placeholder
            return owner, repo, pr_number
    
    raise ValueError("Invalid GitHub URL format")

def main():
    parser = argparse.ArgumentParser(description="Claude PR Reviewer")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Claude model to use")
    args = parser.parse_args()

    try:
        owner, repo, pr_number = parse_github_url(args.pr)
    except ValueError as e:
        print(f"Error parsing URL: {e}")
        sys.exit(1)

    # Get GitHub token from environment
    github_token = os.getenv("GITHUB_TOKEN")
    
    # Fetch the PR diff
    try:
        diff_content = get_pr_diff(owner, repo, pr_number, github_token)
        if not diff_content:
            print("Failed to fetch PR diff")
            sys.exit(1)
    except Exception as e:
        print(f"Error fetching PR diff: {e}")
        sys.exit(1)

    # Analyze with Claude
    try:
        analysis = analyze_code_with_claude(diff_content, args.model)
        print(analysis)
    except Exception as e:
        print(f"Error analyzing code: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()