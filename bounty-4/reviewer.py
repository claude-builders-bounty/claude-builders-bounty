#!/usr/bin/env python3
"""reviewer.py — Claude-powered PR reviewer.

Usage:
  python reviewer.py --pr https://github.com/owner/repo/pull/123
  python reviewer.py --pr <URL> --post
"""

import argparse
import json
import os
import re
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract owner, repo, and PR number from a GitHub PR URL."""
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_diff(owner: str, repo: str, pr_num: int) -> str:
    """Fetch PR diff via GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-reviewer",
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        print(f"Error fetching diff: {e.code}", file=sys.stderr)
        sys.exit(1)


def call_claude(diff: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Send diff to Claude API and return review text."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    prompt = (
        "You are a senior code reviewer. Analyze the following PR diff "
        "and produce a structured Markdown review with these sections:\n\n"
        "## Summary\n2-3 sentence summary of changes.\n\n"
        "## Risks\nList identified risks with severity "
        "(Critical / High / Medium / Low).\n\n"
        "## Suggestions\nNumbered list of improvement suggestions.\n\n"
        "## Confidence\nOverall review confidence: Low / Medium / High.\n\n"
        f"```\n{diff}\n```"
    )

    payload = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )

    try:
        with urlopen(req) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except (HTTPError, KeyError, IndexError) as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        sys.exit(1)


def post_comment(owner: str, repo: str, pr_num: int, body: str) -> None:
    """Post review as a PR comment via gh CLI."""
    try:
        subprocess.run(
            [
                "gh", "pr", "comment", str(pr_num),
                "--repo", f"{owner}/{repo}",
                "--body", body,
            ],
            check=True,
        )
        print("✅ Review posted as PR comment.")
    except subprocess.CalledProcessError:
        print("❌ Failed to post comment. Is gh authenticated?", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Claude PR Reviewer")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--post", action="store_true", help="Post review as PR comment")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Claude model")
    args = parser.parse_args()

    owner, repo, pr_num = parse_pr_url(args.pr)
    print(f"=> Reviewing {owner}/{repo}#{pr_num}")

    diff = fetch_diff(owner, repo, pr_num)
    if not diff:
        print("Error: empty diff", file=sys.stderr)
        sys.exit(1)

    print(f"=> Fetching diff ({len(diff)} chars) ...")
    print(f"=> Calling Claude ({args.model}) ...")

    review = call_claude(diff, args.model)

    print("\n========== PR REVIEW ==========")
    print(review)
    print("================================")

    if args.post:
        post_comment(owner, repo, pr_num, review)


if __name__ == "__main__":
    main()
