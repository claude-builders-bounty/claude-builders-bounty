#!/usr/bin/env python3
"""
claude-review.py - Claude Code sub-agent that reviews a PR and posts a structured comment.

Usage:
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123 --output review.md

Requirements:
    - Python 3.8+
    - requests (pip install requests)
    - ANTHROPIC_API_KEY environment variable

Setup:
    export ANTHROPIC_API_KEY="your-api-key"
    python3 claude-review.py --pr <url>
"""

import argparse
import os
import re
import sys
import urllib.request
import json
from typing import Optional

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"


def extract_pr_info(pr_url: str) -> tuple[str, str, int]:
    """Extract owner, repo, and PR number from a GitHub PR URL."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, pr_url)
    if not match:
        print(f"Error: Invalid PR URL format: {pr_url}", file=sys.stderr)
        print("Expected: https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the diff of a pull request from GitHub."""
    url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "claude-review/1.0"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR diff: HTTP {e.code}", file=sys.stderr)
        if e.code == 404:
            print("PR not found or not accessible", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching PR diff: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_info_api(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR metadata from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "claude-review/1.0"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Warning: Could not fetch PR info: {e}", file=sys.stderr)
        return {}


def call_claude_api(diff: str, pr_title: str, pr_body: str) -> str:
    """Call Claude API to generate a structured PR review."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Truncate diff if too long (API has context limits)
    max_diff_chars = 15000
    truncated_diff = diff[:max_diff_chars]
    if len(diff) > max_diff_chars:
        truncated_diff += "\n\n[... diff truncated due to length ...]"

    system_prompt = """You are an expert code reviewer. Analyze the provided PR diff and generate a structured Markdown review comment.

Your review MUST include these sections:

## Summary
A brief 2-3 sentence summary of what the PR does and its overall quality.

## Identified Risks
- List specific risks or concerns found in the code
- Include security, performance, or maintainability issues
- Be specific about which files/lines have problems

## Improvement Suggestions
- Actionable suggestions for improving the code
- Include code examples where helpful
- Prioritize by impact (high/medium/low)

## Confidence Score
Rate your overall confidence in this PR's quality:
- **High** - Well-structured, follows best practices, minimal concerns
- **Medium** - Acceptable quality with some areas for improvement
- **Low** - Significant issues that should be addressed before merging

Be thorough but constructive. Focus on code quality, not style preferences."""

    user_message = f"""Please review this pull request:

**Title:** {pr_title}

**Description:**
{pr_body[:2000] if pr_body else "No description provided."}

**Diff:**
```diff
{truncated_diff}
```

Generate a structured Markdown review following the format in your instructions."""

    payload = {
        "model": MODEL,
        "max_tokens": 2048,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}]
    }

    try:
        req = urllib.request.Request(
            ANTHROPIC_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"Claude API error: HTTP {e.code} - {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Claude PR Review Agent")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--output", help="Output file for the review (default: print to stdout)")
    parser.add_argument("--model", default=MODEL, help="Claude model to use")
    args = parser.parse_args()

    # Extract PR info
    owner, repo, pr_number = extract_pr_info(args.pr)
    print(f"Analyzing PR #{pr_number} in {owner}/{repo}...")

    # Fetch PR metadata
    pr_info = fetch_pr_info_api(owner, repo, pr_number)
    pr_title = pr_info.get("title", "Unknown PR")
    pr_body = pr_info.get("body", "")

    # Fetch diff
    print("Fetching diff...")
    diff = fetch_pr_diff(owner, repo, pr_number)
    print(f"Diff size: {len(diff)} characters")

    # Generate review
    print("Generating review with Claude...")
    review = call_claude_api(diff, pr_title, pr_body)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"Review saved to {args.output}")
    else:
        print("\n" + "=" * 60)
        print(review)
        print("=" * 60)

    # Check confidence level
    if "**Low**" in review or "Confidence Score: Low" in review:
        print("\nConfidence: LOW - Significant issues identified")
    elif "**Medium**" in review or "Confidence Score: Medium" in review:
        print("\nConfidence: MEDIUM - Some improvements suggested")
    else:
        print("\nConfidence: HIGH - PR looks good")


if __name__ == "__main__":
    main()
