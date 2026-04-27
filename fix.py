#!/usr/bin/env python3
import os
import sys
import argparse
import json
import re
import requests
from anthropic import Anthropic

# Configuration for the Claude model and GitHub API
CLAUDE_MODEL = "claude-3-5-sonnet-20240620" # Using the most capable Sonnet model for code review
GITHUB_API_URL = "https://api.github.com"

class ClaudePRReviewer:
    """Agent that analyzes GitHub PR diffs using the Claude API."""
    
    def __init__(self, github_token=None, anthropic_key=None):
        self.github_token = github_token
        # Initialize Anthropic client with the provided API key
        self.anthropic = Anthropic(api_key=anthropic_key)
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

    def parse_github_url(self, url):
        """Extracts owner, repo, and PR number from a standard GitHub PR URL."""
        match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
        if not match:
            raise ValueError("Invalid GitHub PR URL format provided.")
        return match.groups()

    def get_pr_diff(self, owner, repo, pr_number):
        """Fetches the raw diff of a pull request from the GitHub API."""
        headers = self.headers.copy()
        # Set media type to .diff to get the raw diff content directly
        headers["Accept"] = "application/vnd.github.v3.diff"
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch diff: {response.status_code} {response.text}")
        return response.text

    def get_pr_metadata(self, owner, repo, pr_number):
        """Retrieves PR metadata (title, author, stats) for the review header."""
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch PR metadata: {response.status_code}")
        return response.json()

    def analyze_diff(self, diff_content, metadata):
        """Sends the diff to Claude for structured code analysis."""
        prompt = f"""Analyze the following GitHub Pull Request diff and provide a structured review.

PR Title: {metadata.get('title', 'N/A')}
Author: @{metadata.get('user', {}).get('login', 'unknown')}
Files changed: {metadata.get('changed_files', 'N/A')}

Diff:
{diff_content}

Your review must follow this exact markdown structure:
## 🤖 Automated PR Review
Claude PR: #{metadata.get('number')} - {metadata.get('title')}
Author: @{metadata.get('user', {}).get('login')}
Changes: {metadata.get('changed_files')} files, +{metadata.get('additions')} -{metadata.get('deletions')}

## Summary
[Brief overview of changes]

## ✅ Positive Aspects
- [Identify specific clean code patterns or good logic]

## ⚠️ Potential Issues
### Security
- [Search for credential leaks, injection risks, or weak crypto. Output "None identified" if clean.]
### Performance
- [Identify O(n^2) loops, redundant API calls, or memory leaks. Output "None identified" if clean.]

## 💡 Suggestions
1. [Actionable improvements for readability or logic]

## 🎯 Recommendation
[LGTM / Needs Changes / Requires Discussion] - [Short justification]
"""
        # Execute the request to Claude API with zero temperature for consistency
        message = self.anthropic.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            temperature=0,
            system="You are an elite Senior Software Engineer and Security Auditor. You provide technical, objective, and concise PR reviews.",
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    def post_comment(self, owner, repo, pr_number, body):
        """Posts the generated review as a comment on the GitHub PR."""
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN is required to post comments.")
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        response = requests.post(url, headers=self.headers, json={"body": body})
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to post comment: {response.status_code} {response.text}")
        return response.json()

def main():
    parser = argparse.ArgumentParser(description="Claude PR Review Agent - Automated Code Analysis")
    parser.add_argument("--pr", help="GitHub Pull Request URL (e.g., https://github.com/owner/repo/pull/1)")
    parser.add_argument("--diff", help="Path to a local .diff or .patch file")
    parser.add_argument("--repo", help="Repository 'owner/repo' (required if using --diff)")
    parser.add_argument("--post", action="store_true", help="Post the generated review to GitHub as a comment")

    args = parser.parse_args()

    # Retrieve credentials from environment variables for security
    gh_token = os.getenv("GITHUB_TOKEN")
    ant_key = os.getenv("ANTHROPIC_API_KEY")

    if not ant_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        sys.exit(1)

    reviewer = ClaudePRReviewer(gh_token, ant_key)

    try:
        if args.pr:
            # Handle analysis via GitHub PR URL
            owner, repo, pr_num = reviewer.parse_github_url(args.pr)
            diff_text = reviewer.get_pr_diff(owner, repo, pr_num)
            metadata = reviewer.get_pr_metadata(owner, repo, pr_num)
        elif args.diff:
            # Handle local diff file analysis
            if not args.repo:
                print("Error: --repo 'owner/repo' is required when analyzing a local --diff file.")
                sys.exit(1)
            owner, repo = args.repo.split('/')
            with open(args.diff, 'r') as f:
                diff_text = f.read()
            # Placeholder metadata for local files
            metadata = {
                "title": "Local Diff Analysis", "number": "Local", 
                "user": {"login": "local_user"}, "changed_files": "Unknown",
                "additions": "N/A", "deletions": "N/A"
            }
            pr_num = None
        else:
            parser.print_help()
            sys.exit(1)

        # Process the review using Claude
        print("[*] Analyzing diff with Claude...")
        review_output = reviewer.analyze_diff(diff_text, metadata)
        
        # Output the review to stdout
        print("\n" + "="*40 + "\n")
        print(review_output)
        print("\n" + "="*40 + "\n")

        # Post to GitHub if requested and applicable
        if args.post and pr_num:
            reviewer.post_comment(owner, repo, pr_num, review_output)
            print(f"[+] Successfully posted review to {owner}/{repo} PR #{pr_num}")
        elif args.post and not pr_num:
            print("[!] Cannot post comment: No remote PR number identified (local diff).")

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()