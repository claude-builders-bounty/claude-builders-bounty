#!/usr/bin/env python3
"""Claude Code sub-agent that reviews a GitHub PR diff and posts a structured comment."""

import argparse
import os
import re
import sys
from typing import Optional

import requests


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into owner, repo, and PR number."""
    pattern = r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)'
    match = re.match(pattern, url)
    if not match:
        raise ValueError(f"Invalid PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def get_diff(owner: str, repo: str, pr_number: int, github_token: Optional[str] = None) -> str:
    """Fetch the diff of a GitHub PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "Authorization": f"Bearer {github_token}" if github_token else "",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch PR diff: {response.status_code} - {response.text}")
    return response.text


def call_claude(diff: str, api_key: str) -> str:
    """Call Claude API to analyze the diff and return structured review."""
    prompt = f"""You are a code reviewer. Analyze the following GitHub PR diff and provide a structured Markdown review with exactly these sections:

- **Summary**: 2-3 sentences describing the changes.
- **Identified Risks**: A bullet list of potential issues.
- **Improvement Suggestions**: A bullet list of suggestions for improvement.
- **Confidence Score**: Low / Medium / High based on how confident you are in your analysis.

Diff:
```
{diff}
```
"""

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    if response.status_code != 200:
        raise RuntimeError(f"Claude API error: {response.status_code} - {response.text}")
    return response.json()["content"][0]["text"]


def post_comment(owner: str, repo: str, pr_number: int, comment: str, github_token: str):
    """Post a comment on the PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {github_token}",
    }
    data = {"body": comment}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 201:
        raise RuntimeError(f"Failed to post comment: {response.status_code} - {response.text}")
    print("Comment posted successfully.")


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR using Claude.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--post", action="store_true", help="Post the review as a comment on the PR")
    parser.add_argument("--output", help="File to write the review to (default: stdout)")
    args = parser.parse_args()

    github_token = os.environ.get("GITHUB_TOKEN")
    claude_api_key = os.environ.get("CLAUDE_API_KEY")

    if not claude_api_key:
        print("Error: CLAUDE_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    if args.post and not github_token:
        print("Error: GITHUB_TOKEN environment variable required for --post.", file=sys.stderr)
        sys.exit(1)

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
        print(f"Fetching diff for {owner}/{repo} PR #{pr_number}...")
        diff = get_diff(owner, repo, pr_number, github_token)
        print("Analyzing diff with Claude...")
        review = call_claude(diff, claude_api_key)

        if args.output:
            with open(args.output, "w") as f:
                f.write(review)
            print(f"Review written to {args.output}")
        else:
            print("\n=== Review ===\n")
            print(review)

        if args.post:
            post_comment(owner, repo, pr_number, review, github_token)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
