#!/usr/bin/env python3
"""
Claude Code PR Review Agent

A CLI tool that reviews GitHub pull requests and outputs structured Markdown feedback.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    # Or set GITHUB_TOKEN and ANTHROPIC_API_KEY / NINEROUTER_KEY as environment variables
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from typing import Dict, List, Tuple


class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"

    def _request(self, url: str) -> Dict:
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Claude-Review-Agent"
            }
        )
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            print(f"Error fetching {url}: {e.code} {e.reason}", file=sys.stderr)
            sys.exit(1)

    def get_pr_info(self, repo_owner: str, repo_name: str, pr_number: int) -> Dict:
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        return self._request(url)

    def get_pr_files(self, repo_owner: str, repo_name: str, pr_number: int) -> List[Dict]:
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
        return self._request(url)

    def get_pr_diff(self, repo_owner: str, repo_name: str, pr_number: int) -> str:
        url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3.diff",
                "User-Agent": "Claude-Review-Agent"
            }
        )
        try:
            with urllib.request.urlopen(req) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            print(f"Error fetching diff: {e.code} {e.reason}", file=sys.stderr)
            sys.exit(1)


class ClaudeReviewer:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def review_pr(self, pr_info: Dict, files: List[Dict], diff: str) -> str:
        # Prepare the prompt for Claude
        prompt = self._build_prompt(pr_info, files, diff)

        # Call Claude API or local gateway
        try:
            response = self._call_claude(prompt)
            return response
        except Exception as e:
            print(f"Error calling Claude/9Router API: {e}", file=sys.stderr)
            sys.exit(1)

    def _build_prompt(self, pr_info: Dict, files: List[Dict], diff: str) -> str:
        # Extract relevant information
        title = pr_info.get('title', 'No title')
        description = pr_info.get('body', 'No description')
        user = pr_info.get('user', {}).get('login', 'Unknown')
        changed_files = [f['filename'] for f in files]

        # Limit diff size to avoid token limits
        max_diff_chars = 12000
        if len(diff) > max_diff_chars:
            diff = diff[:max_diff_chars] + "\n\n... (diff truncated)"

        prompt = f"""You are an expert code reviewer. Analyze the following GitHub pull request and provide structured feedback in Markdown format.

PR Information:
- Title: {title}
- Description: {description}
- Author: {user}
- Changed Files: {', '.join(changed_files)}

Diff:
```diff
{diff}
```

Please provide your review in the following Markdown structure:

## Summary
[2-3 sentences summarizing the changes]

## Risks
- [List any potential risks, security issues, bugs, or concerns]

## Improvements
- [List suggestions for improvement]

## Confidence
[Low / Medium / High]

Be concise, constructive, and focus on the most important aspects. Do not output any conversational introduction or wrapping, just start directly with the markdown headers."""
        return prompt

    def _call_claude(self, prompt: str) -> str:
        # Check if we should use local 9Router
        ninerouter_url = os.getenv("NINEROUTER_URL", "http://localhost:20128")
        ninerouter_key = os.getenv("NINEROUTER_KEY", "")

        use_ninerouter = False
        try:
            req = urllib.request.Request(f"{ninerouter_url}/api/health")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    use_ninerouter = True
        except Exception:
            pass

        if use_ninerouter:
            url = f"{ninerouter_url}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
            }
            if ninerouter_key:
                headers["Authorization"] = f"Bearer {ninerouter_key}"

            data = {
                "model": "code",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "stream": False
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            try:
                with urllib.request.urlopen(req) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    return res_data["choices"][0]["message"]["content"]
            except Exception as e:
                print(f"Warning: 9Router call failed ({e}). Falling back to standard Anthropic API...", file=sys.stderr)

        # Standard Anthropic API call as fallback
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["content"][0]["text"]


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """Parse a GitHub PR URL into owner, repo, and PR number."""
    # Example: https://github.com/owner/repo/pull/123
    parts = url.rstrip('/').split('/')
    if len(parts) < 7 or parts[-2] != 'pull':
        raise ValueError("Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123")

    owner = parts[-4]
    repo = parts[-3]
    pr_number = int(parts[-1])
    return owner, repo, pr_number


def main():
    parser = argparse.ArgumentParser(description='Review GitHub PRs using Claude AI')
    parser.add_argument('--pr', required=True, help='GitHub PR URL to review')
    parser.add_argument('--github-token', help='GitHub personal access token (can also use GITHUB_TOKEN env var)')
    parser.add_argument('--anthropic-key', help='Anthropic API key (can also use ANTHROPIC_API_KEY env var)')

    args = parser.parse_args()

    # Get tokens from args or environment
    github_token = args.github_token or os.getenv('GITHUB_TOKEN')
    anthropic_key = args.anthropic_key or os.getenv('ANTHROPIC_API_KEY') or "placeholder-key"

    if not github_token:
        print("Error: GitHub token required. Use --github-token or set GITHUB_TOKEN env var.", file=sys.stderr)
        sys.exit(1)

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Fetch PR data
    github_client = GitHubClient(github_token)
    pr_info = github_client.get_pr_info(owner, repo, pr_number)
    files = github_client.get_pr_files(owner, repo, pr_number)
    diff = github_client.get_pr_diff(owner, repo, pr_number)

    # Review with Claude / 9Router
    reviewer = ClaudeReviewer(anthropic_key)
    review = reviewer.review_pr(pr_info, files, diff)

    # Output the review
    print(review)


if __name__ == '__main__':
    main()
