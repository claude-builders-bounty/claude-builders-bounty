#!/usr/bin/env python3
"""
Claude Code PR Review Agent

Analyzes GitHub pull requests and generates structured Markdown reviews.
"""

import argparse
import os
import re
import sys
import time
from typing import Dict, List, Optional

import requests
from anthropic import Anthropic


class PRReviewer:
    """Reviews GitHub PRs using Claude API."""

    def __init__(self, github_token: Optional[str] = None, claude_api_key: Optional[str] = None, timeout: int = 30):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.claude_api_key = claude_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.timeout = timeout
        
        if not self.claude_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or --claude-api-key required")
        
        self.anthropic = Anthropic(api_key=self.claude_api_key)
        self.github_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.github_token:
            self.github_headers["Authorization"] = f"Bearer {self.github_token}"

    def validate_pr_url(self, pr_url: str) -> tuple[bool, str]:
        """Validate GitHub PR URL format."""
        pattern = r'^https://github\.com/[^/]+/[^/]+/pull/\d+$'
        if not re.match(pattern, pr_url):
            return False, "Invalid GitHub PR URL format. Expected: https://github.com/owner/repo/pull/123"
        return True, ""

    def fetch_pr_diff(self, pr_url: str) -> Dict:
        """Fetch PR details and diff from GitHub with error handling."""
        # Validate URL
        is_valid, error_msg = self.validate_pr_url(pr_url)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Parse owner/repo/pull/number from URL
        parts = pr_url.replace("https://github.com/", "").split("/")
        owner, repo, _, pr_number = parts
        
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        
        try:
            response = requests.get(api_url, headers=self.github_headers, timeout=self.timeout)
            
            # Handle rate limiting
            if response.status_code == 403:
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
                wait_time = max(1, reset_time - int(time.time()))
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                response = requests.get(api_url, headers=self.github_headers, timeout=self.timeout)
            
            response.raise_for_status()
            pr_data = response.json()
            
            # Fetch diff
            diff_url = pr_data["diff_url"]
            diff_response = requests.get(diff_url, headers=self.github_headers, timeout=self.timeout)
            diff_response.raise_for_status()
            
            return {
                "title": pr_data["title"],
                "body": pr_data.get("body", ""),
                "author": pr_data["user"]["login"],
                "additions": pr_data["additions"],
                "deletions": pr_data["deletions"],
                "changed_files": pr_data["changed_files"],
                "diff": diff_response.text,
                "url": pr_url,
            }
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch PR: {str(e)}")

    def analyze_pr(self, pr_data: Dict) -> str:
        """Analyze PR using Claude API with diff truncation warning."""
        diff = pr_data['diff']
        diff_truncated = len(diff) > 10000
        if diff_truncated:
            print(f"Warning: Diff truncated to 10,000 characters (original: {len(diff)} characters)")
        
        prompt = f"""Review this GitHub pull request and provide a structured analysis.

PR Title: {pr_data['title']}
PR Author: {pr_data['author']}
Changes: +{pr_data['additions']} -{pr_data['deletions']} files
Changed Files: {pr_data['changed_files']}

PR Description:
{pr_data['body']}

Diff:
{diff[:10000]}  # Limit to first 10k characters

Provide a structured review in the following format:

## Summary
[2-3 sentences summarizing the changes]

## Risks
- [Risk 1]
- [Risk 2]
- ...

## Improvements
- [Suggestion 1]
- [Suggestion 2]
- ...

## Confidence
[Low / Medium / High]

Focus on:
- Code quality and best practices
- Potential bugs or edge cases
- Security concerns
- Performance implications
- Documentation completeness
"""

        try:
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            return f"Error analyzing PR: {str(e)}"

    def format_review(self, analysis: str, pr_data: Dict) -> str:
        """Format the review as a GitHub comment."""
        return f"""## 🤖 Claude Code PR Review

**PR:** {pr_data['url']}
**Author:** @{pr_data['author']}
**Changes:** +{pr_data['additions']} -{pr_data['deletions']} ({pr_data['changed_files']} files)

---

{analysis}

---

*Generated by Claude Code PR Review Agent*
"""

    def review_pr(self, pr_url: str) -> str:
        """Full review pipeline."""
        print(f"Fetching PR: {pr_url}")
        pr_data = self.fetch_pr_diff(pr_url)
        print(f"Analyzing {pr_data['changed_files']} files...")
        
        analysis = self.analyze_pr(pr_data)
        review = self.format_review(analysis, pr_data)
        
        return review


def main():
    parser = argparse.ArgumentParser(description="Review GitHub PRs with Claude AI")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--github-token", help="GitHub personal access token")
    parser.add_argument("--claude-api-key", help="Anthropic API key")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds (default: 30)")
    
    args = parser.parse_args()
    
    reviewer = PRReviewer(
        github_token=args.github_token,
        claude_api_key=args.claude_api_key,
        timeout=args.timeout,
    )
    
    review = reviewer.review_pr(args.pr)
    
    if args.output:
        # Ensure .md extension
        output_file = args.output if args.output.endswith('.md') else f"{args.output}.md"
        with open(output_file, "w") as f:
            f.write(review)
        print(f"Review saved to {output_file}")
    else:
        print(review)


if __name__ == "__main__":
    main()