#!/usr/bin/env python3
"""
Claude Code PR Reviewer

A CLI tool that reviews GitHub PRs and generates structured Markdown feedback.
"""

import argparse
import os
import sys
import requests
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Review:
    summary: str
    risks: List[str]
    suggestions: List[str]
    confidence: str  # Low, Medium, High


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """Parse GitHub PR URL into owner, repo, pr_number"""
    # Handle both HTTPS and SSH URL formats
    if url.startswith("https://github.com/"):
        parts = url.replace("https://github.com/", "").strip("/").split("/")
    else:
        raise ValueError("Unsupported GitHub URL format")
    
    if len(parts) >= 4 and parts[2] == "pull":
        owner = parts[0]
        repo = parts[1]
        pr_number = int(parts[3])
        return owner, repo, pr_number
    else:
        raise ValueError("Invalid GitHub PR URL")


def get_github_token() -> str:
    """Get GitHub token from environment variable"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return token


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Fetch the diff of a pull request"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get PR details
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    response = requests.get(pr_url, headers=headers)
    response.raise_for_status()
    pr_data = response.json()
    
    # Get diff
    diff_url = pr_data["diff_url"]
    diff_response = requests.get(diff_url, headers={"Authorization": f"Bearer {token}"})
    diff_response.raise_for_status()
    
    return diff_response.text


def analyze_code_with_claude(diff: str, token: str) -> Review:
    """Use Claude API to analyze code changes and return structured review"""
    # This is a simplified implementation
    # In a real implementation, you would call the Claude API here
    # For now, we'll return a mock response
    
    # Mock analysis - in practice, this would be replaced with actual Claude API call
    summary = "This pull request modifies the core functionality of the application by updating the data processing module and adding new validation checks. The changes improve error handling and add support for additional input formats."
    
    risks = [
        "The new validation logic may be too restrictive and could block previously valid inputs",
        "Error handling changes might mask underlying issues rather than fixing them",
        "Performance impact of additional validation checks not evaluated"
    ]
    
    suggestions = [
        "Add unit tests to cover the new validation logic",
        "Consider making validation rules configurable rather than hardcoded",
        "Add logging for rejected inputs to help with debugging"
    ]
    
    confidence = "Medium"
    
    return Review(
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence
    )


def format_markdown_review(review: Review) -> str:
    """Format the review as Markdown"""
    md = "# Code Review\n\n"
    md += f"## Summary\n{review.summary}\n\n"
    md += "## Identified Risks\n"
    for risk in review.risks:
        md += f"- {risk}\n"
    md += "\n"
    md += "## Improvement Suggestions\n"
    for suggestion in review.suggestions:
        md += f"- {suggestion}\n"
    md += f"\n## Confidence: {review.confidence}\n"
    return md


def post_comment_to_pr(owner: str, repo: str, pr_number: int, comment: str, token: str):
    """Post the review as a comment to the PR"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    payload = {"body": comment}
    
    response = requests.post(comment_url, headers=headers, json=payload)
    response.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR with Claude Code")
    parser.add_argument("--pr", help="GitHub PR URL", required=True)
    parser.add_argument("--comment", help="Post review as a comment to the PR", action="store_true")
    
    args = parser.parse_args()
    
    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error parsing PR URL: {e}")
        sys.exit(1)
    
    try:
        token = get_github_token()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    try:
        diff = fetch_pr_diff(owner, repo, pr_number, token)
    except Exception as e:
        print(f"Error fetching PR diff: {e}")
        sys.exit(1)
    
    # Analyze with Claude
    review = analyze_code_with_claude(diff, token)
    
    # Format as markdown
    markdown_review = format_markdown_review(review)
    
    if args.comment:
        try:
            post_comment_to_pr(owner, repo, pr_number, markdown_review, token)
            print("Review posted as a comment to the PR.")
        except Exception as e:
            print(f"Error posting comment: {e}")
            print("\nReview Output:\n")
            print(markdown_review)
    else:
        print(markdown_review)


if __name__ == "__main__":
    main()