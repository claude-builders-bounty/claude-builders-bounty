#!/usr/bin/env python3
"""
claude-review — Claude Code sub-agent that reviews a GitHub PR and returns
a structured Markdown comment.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import json
import urllib.request
import urllib.error
from typing import Optional


CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_DIFF_CHARS = 12_000

REVIEW_PROMPT = """You are a senior software engineer conducting a pull request review.
You will receive the PR title, description, and diff. Return a structured Markdown review.

## PR Information
Title: {title}
Author: {author}
Base → Head: {base} → {head}
Files changed: {files_changed}

## Diff (truncated to {max_chars} chars if large)
```diff
{diff}
```

## Your Task
Return ONLY this Markdown structure — no preamble, no trailing text:

### Summary
(2–3 sentences describing what this PR does)

### Risks
- (list every risk you identify — security, correctness, performance, breaking changes)
- If none: `None identified`

### Improvement Suggestions
- (actionable suggestions — code style, missing tests, edge cases)
- If none: `None`

### Confidence Score
(One of: **Low** | **Medium** | **High**)
Rationale: (one sentence explaining the score)
"""


def _api_get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "claude-review/1.0",
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def _api_get_text(url: str, token: str) -> str:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "claude-review/1.0",
    })
    with urllib.request.urlopen(req) as r:
        return r.read().decode("utf-8", errors="replace")


def fetch_pr(pr_url: str, gh_token: str) -> tuple[dict, str]:
    """Return (pr_meta, diff_text)."""
    m = re.match(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_url)
    if not m:
        raise ValueError(f"Cannot parse PR URL: {pr_url}")
    repo, number = m.group(1), m.group(2)
    meta = _api_get(f"https://api.github.com/repos/{repo}/pulls/{number}", gh_token)
    diff = _api_get_text(f"https://api.github.com/repos/{repo}/pulls/{number}", gh_token)
    return meta, diff


def call_claude(prompt: str, api_key: str) -> str:
    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        body = json.loads(r.read())
    return body["content"][0]["text"]


def review_pr(pr_url: str, gh_token: str, api_key: str) -> str:
    meta, diff = fetch_pr(pr_url, gh_token)
    diff_truncated = diff[:MAX_DIFF_CHARS] + ("\n... (truncated)" if len(diff) > MAX_DIFF_CHARS else "")
    prompt = REVIEW_PROMPT.format(
        title=meta.get("title", ""),
        author=meta.get("user", {}).get("login", "unknown"),
        base=meta.get("base", {}).get("ref", "?"),
        head=meta.get("head", {}).get("ref", "?"),
        files_changed=meta.get("changed_files", "?"),
        max_chars=MAX_DIFF_CHARS,
        diff=diff_truncated,
    )
    review = call_claude(prompt, api_key)
    header = f"## Claude Code PR Review\n\n**PR:** {pr_url}  \n**Model:** `{CLAUDE_MODEL}`\n\n---\n\n"
    return header + review


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Claude Code PR reviewer — structured Markdown review via Claude API"
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--output", help="Write review to this file (default: stdout)")
    args = parser.parse_args()

    gh_token: Optional[str] = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    api_key: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")

    if not gh_token:
        sys.exit("Error: set GITHUB_TOKEN or GH_TOKEN environment variable")
    if not api_key:
        sys.exit("Error: set ANTHROPIC_API_KEY environment variable")

    try:
        review = review_pr(args.pr, gh_token, api_key)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:200]}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review)
        print(f"Review written to {args.output}")
    else:
        print(review)


if __name__ == "__main__":
    main()
