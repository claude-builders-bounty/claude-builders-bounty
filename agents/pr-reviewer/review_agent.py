
#!/usr/bin/env python3
"""
PR Review Agent - Automated code review for GitHub Pull Requests

This script processes code diffs from a GitHub PR, analyzes them using an LLM API,
and generates a structured Markdown review report.
"""

import os
import sys
import json
import subprocess
import requests
from typing import Dict, List, Optional, Tuple

# Configuration
LLM_API_URL = "https://api.openai.com/v1/chat/completions"  # Replace with actual LLM API endpoint
LLM_MODEL = "gpt-4"  # Replace with preferred model
GITHUB_API_URL = "https://api.github.com"

def get_pr_diff(repo: str, pr_number: int, github_token: str) -> str:
    """
    Fetch the diff for a specific PR using GitHub API.

    Args:
        repo: Repository in format 'owner/repo'
        pr_number: Pull request number
        github_token: GitHub access token

    Returns:
        The diff as a string
    """
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3.diff"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR diff: {response.status_code} - {response.text}")

    return response.text

def get_git_diff() -> str:
    """
    Get the git diff from the current working directory.

    Returns:
        The diff as a string
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--unified=0", "HEAD^"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to get git diff: {e.stderr}")

def analyze_code_diff(diff: str, llm_api_key: str) -> str:
    """
    Analyze the code diff using LLM API and generate a review.

    Args:
        diff: The code diff to analyze
        llm_api_key: API key for the LLM service

    Returns:
        A structured Markdown review report
    """
    if not diff:
        return "No changes detected in the PR."

    system_prompt = """
    You are an expert code reviewer. Analyze the following code diff and provide a detailed review.
    Your review should be structured in Markdown format with the following sections:

    ## Summary of Changes
    - Brief summary of what the changes do

    ## Critical Issues
    - Any critical bugs, security vulnerabilities, or breaking changes
    - List each issue with file and line references

    ## Code Quality & Style
    - Code style violations
    - Readability improvements
    - Best practice violations

    ## Performance Optimizations
    - Potential performance improvements
    - Inefficient algorithms or data structures

    ## Documentation
    - Missing or inadequate documentation
    - Suggestions for improving documentation

    ## Testing
    - Missing test cases
    - Suggestions for improving test coverage

    For each issue, provide:
    1. File and line number (if applicable)
    2. The problematic code snippet
    3. A clear explanation of the issue
    4. A suggested fix (if applicable)

    Be thorough but constructive in your feedback.
    """

    user_prompt = f"""
    Please review the following code diff:

    {diff}
    """

    headers = {
        "Authorization": f"Bearer {llm_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(LLM_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "Failed to generate review: No response from LLM API"
    except Exception as e:
        return f"Failed to generate review: {str(e)}"

def post_review_comment(
    repo: str,
    pr_number: int,
    comment: str,
    github_token: str
) -> bool:
    """
    Post a review comment on a GitHub PR.

    Args:
        repo: Repository in format 'owner/repo'
        pr_number: Pull request number
        comment: The review comment to post
        github_token: GitHub access token

    Returns:
        True if successful, False otherwise
    """
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}/reviews"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    payload = {
        "body": comment,
        "event": "COMMENT"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to post review comment: {str(e)}", file=sys.stderr)
        return False

def main():
    """
    Main entry point for the PR review agent.
    """
    # Get environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    llm_api_key = os.getenv("LLM_API_KEY")
    repo = os.getenv("GITHUB_REPOSITORY")
    pr_number = os.getenv("PR_NUMBER")

    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not llm_api_key:
        print("Error: LLM_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    if not repo:
        print("Error: GITHUB_REPOSITORY environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        # Get PR diff
        if pr_number:
            pr_number = int(pr_number)
            diff = get_pr_diff(repo, pr_number, github_token)
        else:
            # Fallback to git diff if PR_NUMBER not provided
            diff = get_git_diff()

        # Analyze the diff
        review = analyze_code_diff(diff, llm_api_key)

        # Post the review
        if pr_number:
            success = post_review_comment(repo, pr_number, review, github_token)
            if not success:
                print("Failed to post review comment", file=sys.stderr)
                sys.exit(1)
        else:
            # Print to stdout if not posting to GitHub
            print(review)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
