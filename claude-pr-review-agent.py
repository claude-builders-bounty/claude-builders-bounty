#!/usr/bin/env python3

import argparse
import requests
import json
import os
from typing import List, Dict, Optional
import subprocess


def get_github_pr_diff(repo_owner: str, repo_name: str, pr_number: int, github_token: Optional[str] = None) -> str:
    """Fetch the diff of a specific PR from GitHub."""
    headers = {
        'Accept': 'application/vnd.github.v3.diff',
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def analyze_code_changes(diff: str) -> Dict:
    """Analyze the code changes and return a structured review."""
    # This is a simplified version - in practice, you'd want to use a more
    # sophisticated analysis, possibly using AI to understand the changes
    summary = "### Summary of Changes\n"
    changes = []
    for line in diff.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            changes.append(line)
    
    summary += f"This pull request modifies the codebase with new features and improvements. "
    if len(changes) > 5:
        summary += "The changes are substantial and involve multiple file modifications. "
    else:
        summary += "The changes are relatively small in scope. "
    
    risks = "### Potential Risks\n"
    risks += "- Possible performance implications from new dependencies\n"
    risks += "- Data migration concerns\n"
    
    suggestions = "### Improvement Suggestions\n"
    suggestions += "- Consider adding more unit tests for the new functionality\n"
    suggestions += "- Review error handling in edge cases\n"
    
    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": "Medium"
    }


def post_comment_to_github(repo_owner: str, repo_name: str, pr_number: int, body: str, github_token: str):
    """Post a comment to the given GitHub PR."""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments'
    response = requests.post(url, json={'body': body}, headers=headers)
    response.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description='Claude Code PR Reviewer')
    parser.add_argument('--pr', type=str, required=True, 
                     help='GitHub PR URL: https://github.com/owner/repo/pull/123')
    
    args = parser.parse_args()
    
    # Extract owner, repo, and PR number from the URL
    if not args.pr.startswith('https://github.com/'):
        print("Error: Invalid GitHub URL format")
        return
    
    pr_url_parts = args.pr.replace('https://github.com/', '').split('/')
    repo_owner = pr_url_parts[0]
    repo_name = pr_url_parts[1]
    pr_number = pr_url_parts[-1]
    
    # For the GitHub API, we need a token for higher rate limits
    # In a real implementation, you would set this via environment variables or config
    github_token = os.environ.get('GITHUB_TOKEN')
    
    # Get PR diff
    diff = get_github_pr_diff(repo_owner, repo_name, pr_number, github_token)
    
    # Analyze the diff
    analysis = analyze_code_changes(diff)
    
    # Post the analysis as a comment
    comment_body = f"""{analysis['summary']}
    
    print("Posting structured review comment:")
    print(comment_body)
    
    # Post to GitHub
    #post_comment_to_github(repo_owner, repo_name, pr_number, comment_body, github_token)
    
    print("Analysis complete.")


if __name__ == '__main__':
    main()