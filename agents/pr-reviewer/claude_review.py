#!/usr/bin/env python3
"""
claude-review: AI-powered GitHub PR reviewer using Claude.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
"""

import argparse
import os
import re
import sys

import anthropic
import requests


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse owner, repo, and PR number from a GitHub PR URL."""
    pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url.strip())
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {url!r}\nExpected format: https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return owner, repo, int(number)


def fetch_pr_data(owner: str, repo: str, number: int, token: str | None) -> dict:
    """Fetch PR metadata and diff from GitHub API."""
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Fetch PR metadata
    meta_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    meta_resp = requests.get(meta_url, headers=headers, timeout=30)
    if meta_resp.status_code == 404:
        raise RuntimeError(f"PR not found: {owner}/{repo}#{number}. Check the URL and ensure GITHUB_TOKEN is set for private repos.")
    if meta_resp.status_code == 401:
        raise RuntimeError("GitHub authentication failed. Set a valid GITHUB_TOKEN environment variable.")
    meta_resp.raise_for_status()
    pr = meta_resp.json()

    # Fetch diff
    diff_headers = {**headers, "Accept": "application/vnd.github.v3.diff"}
    diff_resp = requests.get(meta_url, headers=diff_headers, timeout=30)
    diff_resp.raise_for_status()
    diff = diff_resp.text

    return {
        "title": pr["title"],
        "body": pr.get("body") or "",
        "author": pr["user"]["login"],
        "base": pr["base"]["ref"],
        "head": pr["head"]["ref"],
        "changed_files": pr["changed_files"],
        "additions": pr["additions"],
        "deletions": pr["deletions"],
        "diff": diff,
    }


def build_prompt(owner: str, repo: str, number: int, pr: dict) -> str:
    """Build the review prompt for Claude."""
    diff_snippet = pr["diff"]
    # Keep diff under ~80k chars to stay within context limits
    if len(diff_snippet) > 80_000:
        diff_snippet = diff_snippet[:80_000] + "\n\n[... diff truncated for length ...]"

    return f"""You are an expert code reviewer. Review the following GitHub pull request and produce a structured Markdown review.

## Pull Request Info
- **Repo:** {owner}/{repo}
- **PR:** #{number} — {pr['title']}
- **Author:** {pr['author']}
- **Base ← Head:** `{pr['base']}` ← `{pr['head']}`
- **Changes:** +{pr['additions']} / -{pr['deletions']} across {pr['changed_files']} file(s)

## PR Description
{pr['body'] if pr['body'] else '_No description provided._'}

## Diff
```diff
{diff_snippet}
```

---

Produce a review using **exactly** this Markdown structure (do not add extra top-level sections):

## Summary
[2-3 sentences describing what this PR does and its overall approach]

## Identified Risks
- [risk 1]
- [risk 2]
- ...

## Improvement Suggestions
- [suggestion 1]
- [suggestion 2]
- ...

## Confidence Score
**[Low / Medium / High]** — [one sentence explaining the confidence level based on diff clarity, test coverage, and scope]

Be specific and actionable. Reference file names or line context where helpful. If risks or suggestions are none, say so explicitly with a single "- None identified." bullet."""


def call_claude(prompt: str, api_key: str) -> str:
    """Send prompt to Claude and return the response text."""
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="AI-powered GitHub PR reviewer using Claude.",
    )
    parser.add_argument(
        "--pr",
        required=True,
        metavar="URL",
        help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    github_token = os.environ.get("GITHUB_TOKEN")

    try:
        owner, repo, number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching PR {owner}/{repo}#{number}...", file=sys.stderr)
    try:
        pr_data = fetch_pr_data(owner, repo, number, github_token)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.HTTPError as e:
        print(f"Error fetching PR from GitHub: {e}", file=sys.stderr)
        sys.exit(1)

    print("Sending diff to Claude for review...", file=sys.stderr)
    prompt = build_prompt(owner, repo, number, pr_data)
    try:
        review = call_claude(prompt, api_key)
    except anthropic.AuthenticationError:
        print("Error: Invalid ANTHROPIC_API_KEY.", file=sys.stderr)
        sys.exit(1)
    except anthropic.APIError as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        sys.exit(1)

    # Header with PR link
    header = f"# PR Review: [{owner}/{repo}#{number}]({args.pr})\n\n"
    print(header + review)


if __name__ == "__main__":
    main()
