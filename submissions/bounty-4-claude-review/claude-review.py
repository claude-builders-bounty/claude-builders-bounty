#!/usr/bin/env python3
"""
claude-review — PR reviewer powered by Claude API
Usage: python claude-review.py --pr https://github.com/owner/repo/pull/123
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def github_request(url: str) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "claude-review/1.0"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def github_diff(url: str) -> str:
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_pr_url(url: str) -> tuple[str, str, str]:
    """Extract owner, repo, PR number from GitHub PR URL."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip())
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), m.group(3)


def claude_review(pr_title: str, pr_body: str, diff: str, pr_url: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    # Truncate diff if very large (Claude context limit)
    max_diff = 40000
    if len(diff) > max_diff:
        diff = diff[:max_diff] + "\n\n[... diff truncated for length ...]"

    prompt = f"""You are a senior software engineer performing a thorough code review.

PR: {pr_url}
Title: {pr_title}
Description: {pr_body or "(none)"}

Diff:
```diff
{diff}
```

Provide a structured review in exactly this Markdown format:

## Summary
(2-3 sentences describing what this PR does)

## Identified Risks
- (list each risk — security, performance, correctness, edge cases, breaking changes)
- (if none, write "No significant risks identified")

## Improvement Suggestions
- (specific, actionable suggestions with line references where possible)
- (if none, write "Code looks clean — no suggestions")

## Confidence Score
**[Low / Medium / High]** — (one sentence explaining why)

Be direct. No filler. Flag real issues. Don't invent problems that don't exist."""

    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        d = json.loads(resp.read())
    return d["content"][0]["text"]


def main():
    parser = argparse.ArgumentParser(
        description="Review a GitHub PR using Claude API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python claude-review.py --pr https://github.com/owner/repo/pull/42
  GITHUB_TOKEN=ghp_... python claude-review.py --pr https://github.com/owner/repo/pull/42
        """,
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--post", action="store_true", help="Post review as PR comment (requires GITHUB_TOKEN)")
    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        print("  export ANTHROPIC_API_KEY=sk-ant-...", file=sys.stderr)
        sys.exit(1)

    owner, repo, pr_num = parse_pr_url(args.pr)
    api_base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"

    print(f"Fetching PR #{pr_num} from {owner}/{repo}...")
    pr_data = github_request(api_base)
    pr_title = pr_data.get("title", "")
    pr_body = pr_data.get("body", "") or ""

    print("Fetching diff...")
    diff = github_diff(api_base)

    if not diff.strip():
        print("Warning: diff is empty — PR may have no file changes", file=sys.stderr)

    print("Sending to Claude for review...\n")
    review = claude_review(pr_title, pr_body, diff, args.pr)

    print("=" * 60)
    print(f"# Code Review: {pr_title}")
    print(f"**PR:** {args.pr}")
    print()
    print(review)
    print("=" * 60)

    if args.post:
        if not GITHUB_TOKEN:
            print("Error: --post requires GITHUB_TOKEN", file=sys.stderr)
            sys.exit(1)
        comment_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_num}/comments"
        body = f"## 🤖 Claude Code Review\n\n{review}\n\n---\n*Reviewed by [claude-review](https://github.com/leegier/claude-builders-bounty/tree/main/submissions/bounty-4-claude-review)*"
        payload = json.dumps({"body": body}).encode()
        req = urllib.request.Request(
            comment_url,
            data=payload,
            headers={
                "Authorization": f"token {GITHUB_TOKEN}",
                "Content-Type": "application/json",
                "User-Agent": "claude-review/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            d = json.loads(resp.read())
        print(f"\nPosted comment: {d['html_url']}")


if __name__ == "__main__":
    main()
