#!/usr/bin/env python3
"""
Claude PR Review Agent — reviews a GitHub PR and outputs structured Markdown.

Usage:
    python claude-review.py --pr https://github.com/owner/repo/pull/123
    python claude-review.py --pr https://github.com/owner/repo/pull/123 --post
    python claude-review.py --diff ./changes.diff
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: 'requests' package required. Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("Error: 'anthropic' package required. Run: pip install -r requirements.txt")
    sys.exit(1)


REVIEW_PROMPT = """You are an expert code reviewer. Analyze the following PR diff and produce a structured Markdown review.

The PR title is: {title}
The PR description is:
{description}

The diff is:
```diff
{diff}
```

Produce your review in EXACTLY this Markdown format:

## 🤖 PR Review

### Summary
<Write 2–3 sentences summarizing what this PR changes and why.>

### ⚠️ Risks
<List specific risks or potential bugs. Use bullet points. If none, write "- No significant risks identified.">
- Risk 1
- Risk 2

### 💡 Suggestions
<List improvement suggestions. Use bullet points. If none, write "- No additional suggestions.">
- Suggestion 1
- Suggestion 2

### Confidence: **Low / Medium / High**
<Pick one confidence level based on how well you understood the changes and how thorough your review is.>

IMPORTANT: Output ONLY the Markdown review. No extra commentary.
"""


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    pattern = r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url.strip().rstrip("/"))
    if not match:
        raise ValueError(
            f"Invalid PR URL: {url}\nExpected format: https://github.com/owner/repo/pull/123"
        )
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_info(owner: str, repo: str, pr_number: int, token: str) -> dict:
    """Fetch PR metadata from GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = requests.get(api_url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str) -> str:
    """Fetch the diff of a PR from GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "Authorization": f"token {token}",
    }
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = requests.get(api_url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def review_with_claude(
    diff: str,
    title: str = "N/A",
    description: str = "N/A",
    model: str = "claude-sonnet-4-20250514",
) -> str:
    """Send the diff to Claude and get a structured review."""
    client = anthropic.Anthropic()

    # Truncate very large diffs
    max_diff_chars = 50000
    if len(diff) > max_diff_chars:
        diff = diff[:max_diff_chars] + "\n... [truncated]"

    prompt = REVIEW_PROMPT.format(
        title=title,
        description=description[:5000] if description else "N/A",
        diff=diff,
    )

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


def post_comment(
    owner: str, repo: str, pr_number: int, body: str, token: str
) -> dict:
    """Post a review comment on a GitHub PR."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    resp = requests.post(api_url, headers=headers, json={"body": body}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(
        description="Claude PR Review Agent — review a GitHub PR and output structured Markdown."
    )
    parser.add_argument(
        "--pr",
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)",
    )
    parser.add_argument(
        "--diff",
        help="Path to a local diff file to review",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post the review as a comment on the PR",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--output",
        help="Write the review to a file instead of stdout",
    )

    args = parser.parse_args()

    if not args.pr and not args.diff:
        parser.error("Either --pr or --diff is required")

    github_token = os.environ.get("GITHUB_TOKEN", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not anthropic_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    # Get the diff
    if args.diff:
        diff_path = Path(args.diff)
        if not diff_path.exists():
            print(f"Error: diff file not found: {args.diff}", file=sys.stderr)
            sys.exit(1)
        diff = diff_path.read_text()
        title = "Local diff"
        description = "N/A"
        owner = repo = ""
        pr_number = 0
    else:
        if not github_token:
            print("Error: GITHUB_TOKEN environment variable is required for --pr.", file=sys.stderr)
            sys.exit(1)

        try:
            owner, repo, pr_number = parse_pr_url(args.pr)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        print(f"Fetching PR #{pr_number} from {owner}/{repo}...")

        try:
            pr_info = fetch_pr_info(owner, repo, pr_number, github_token)
        except requests.HTTPError as e:
            print(f"Error fetching PR info: {e}", file=sys.stderr)
            sys.exit(1)

        title = pr_info.get("title", "N/A")
        description = pr_info.get("body", "") or "N/A"

        try:
            diff = fetch_pr_diff(owner, repo, pr_number, github_token)
        except requests.HTTPError as e:
            print(f"Error fetching PR diff: {e}", file=sys.stderr)
            sys.exit(1)

    # Review with Claude
    print("Analyzing PR with Claude...")
    review = review_with_claude(diff, title=title, description=description, model=args.model)

    # Output
    if args.output:
        Path(args.output).write_text(review)
        print(f"Review written to {args.output}")
    else:
        print("\n" + review)

    # Post comment if requested
    if args.post and args.pr:
        if not github_token:
            print("Error: GITHUB_TOKEN required to post comments.", file=sys.stderr)
            sys.exit(1)
        print(f"Posting review comment on {owner}/{repo}#{pr_number}...")
        try:
            post_comment(owner, repo, pr_number, review, github_token)
            print("Comment posted successfully!")
        except requests.HTTPError as e:
            print(f"Error posting comment: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
