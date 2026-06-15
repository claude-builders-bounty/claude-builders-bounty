#!/usr/bin/env python3
"""
claude-review — Claude Code sub-agent that reviews a GitHub PR.
Usage: python3 pr-review.py <PR_URL>
       python3 pr-review.py https://github.com/owner/repo/pull/123
"""

import sys
import os
import json
import re
import subprocess
import argparse
from urllib.request import urlopen, Request
from urllib.error import URLError

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
MODEL = "claude-sonnet-4-6"

REVIEW_PROMPT = """You are a senior software engineer performing a thorough code review.

PR Title: {title}
PR Description: {body}

Diff:
{diff}

Files changed: {files}

Produce a structured review in this EXACT markdown format:

## Summary
<2-3 sentences describing what this PR does and its overall approach>

## Risks
<bullet list of potential issues, bugs, security concerns, or unintended side effects. If none, write "None identified.">

## Suggestions
<bullet list of concrete improvement suggestions with brief explanations. Focus on actionable items.>

## Confidence
**Overall assessment**: <one of: Approve / Request Changes / Needs Discussion>
**Confidence**: <Low / Medium / High>
**Reason**: <one sentence explaining the confidence level>

Be specific and reference actual code/line numbers where possible. Prioritize correctness, security, and maintainability."""


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not m:
        raise ValueError(f"Not a valid GitHub PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def gh_get(path: str) -> dict | list:
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = Request(url, headers=headers)
    with urlopen(req) as r:
        return json.loads(r.read())


def gh_get_diff(owner: str, repo: str, pr_num: int) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {
        "Accept": "application/vnd.github.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = Request(url, headers=headers)
    with urlopen(req) as r:
        return r.read().decode("utf-8", errors="replace")


def call_claude(prompt: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    with urlopen(req) as r:
        data = json.loads(r.read())
    return data["content"][0]["text"]


def review_pr(pr_url: str) -> str:
    owner, repo, pr_num = parse_pr_url(pr_url)
    print(f"Fetching PR #{pr_num} from {owner}/{repo}...", file=sys.stderr)

    pr = gh_get(f"/repos/{owner}/{repo}/pulls/{pr_num}")
    files_data = gh_get(f"/repos/{owner}/{repo}/pulls/{pr_num}/files")

    title = pr.get("title", "")
    body = pr.get("body", "") or "(no description)"
    files = [f["filename"] for f in files_data]

    print(f"Fetching diff ({len(files)} files changed)...", file=sys.stderr)
    diff = gh_get_diff(owner, repo, pr_num)

    # Truncate diff if very large (keep first 12k chars)
    if len(diff) > 12000:
        diff = diff[:12000] + "\n\n[... diff truncated for length ...]"

    prompt = REVIEW_PROMPT.format(
        title=title,
        body=body[:800],
        diff=diff,
        files=", ".join(files[:20]) + ("..." if len(files) > 20 else "")
    )

    print("Calling Claude API...", file=sys.stderr)
    review = call_claude(prompt)

    header = f"# PR Review: {owner}/{repo}#{pr_num}\n\n**{title}**\n\n---\n\n"
    return header + review


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR using Claude")
    parser.add_argument("pr_url", help="GitHub PR URL (https://github.com/owner/repo/pull/N)")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")
    args = parser.parse_args()

    try:
        result = review_pr(args.pr_url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
