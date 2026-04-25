#!/usr/bin/env python3
"""
claude-review — Claude Code sub-agent that reviews a GitHub PR and posts a structured comment.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --pr https://github.com/owner/repo/pull/123 --post

Requirements:
    pip install anthropic requests
    export ANTHROPIC_API_KEY=sk-ant-...
    export GITHUB_TOKEN=ghp_...  (optional, for private repos and posting)
"""
import argparse
import os
import re
import sys
from urllib.parse import urlparse

import requests

try:
    import anthropic
except ImportError:
    print("Error: Run `pip install anthropic requests` first.", file=sys.stderr)
    sys.exit(1)


REVIEW_PROMPT = """You are an expert code reviewer. Analyze the following GitHub PR diff and produce a structured review.

PR Title: {title}
PR Description: {description}

Diff:
{diff}

Output ONLY the following Markdown structure (no preamble):

## Summary
<2-3 sentences describing what this PR does>

## Risks
<bullet list of potential issues, regressions, or concerns — be specific>

## Suggestions
<bullet list of concrete improvements — include file/line references where possible>

## Confidence
**Level:** <Low | Medium | High>
**Reasoning:** <one sentence explaining why>
"""

MAX_DIFF_CHARS = 40_000  # ~10k tokens


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Return (owner, repo, pr_number) from a GitHub PR URL."""
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Not a valid GitHub PR URL: {url!r}")
    return m.group(1), m.group(2), int(m.group(3))


def get_pr_data(owner: str, repo: str, pr_number: int, token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    r = requests.get(pr_url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def get_pr_diff(owner: str, repo: str, pr_number: int, token: str | None) -> str:
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if token:
        headers["Authorization"] = f"token {token}"

    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    r = requests.get(diff_url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text


def review_with_claude(title: str, description: str, diff: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)

    # Truncate diff if too long
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n[...diff truncated for length...]"

    prompt = REVIEW_PROMPT.format(
        title=title,
        description=description or "(no description provided)",
        diff=diff,
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def post_comment(owner: str, repo: str, pr_number: int, body: str, token: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    r = requests.post(url, json={"body": body}, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()["html_url"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review a GitHub PR with Claude and output structured Markdown."
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument(
        "--post", action="store_true", help="Post review as a PR comment (requires GITHUB_TOKEN)"
    )
    parser.add_argument("--output", help="Write review to file instead of stdout")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    token = os.environ.get("GITHUB_TOKEN")

    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching PR {owner}/{repo}#{pr_number}...", file=sys.stderr)
    pr_data = get_pr_data(owner, repo, pr_number, token)
    diff = get_pr_diff(owner, repo, pr_number, token)

    title = pr_data.get("title", "")
    description = pr_data.get("body", "") or ""

    print("Analyzing with Claude...", file=sys.stderr)
    review = review_with_claude(title, description, diff, api_key)

    header = f"## 🤖 Claude Code Review — [{owner}/{repo}#{pr_number}]({args.pr})\n\n"
    full_review = header + review

    if args.output:
        with open(args.output, "w") as f:
            f.write(full_review)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(full_review)

    if args.post:
        if not token:
            print("Error: --post requires GITHUB_TOKEN to be set.", file=sys.stderr)
            sys.exit(1)
        comment_url = post_comment(owner, repo, pr_number, full_review, token)
        print(f"\nPosted: {comment_url}", file=sys.stderr)


if __name__ == "__main__":
    main()
