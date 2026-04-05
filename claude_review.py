#!/usr/bin/env python3
"""Claude Code PR Review Agent — analyzes a GitHub PR diff and outputs structured Markdown review."""

import argparse
import json
import re
import subprocess
import sys

import anthropic

MODEL = "claude-3-5-haiku-20241022"
MAX_DIFF_CHARS = 80_000


def parse_pr_url(url: str) -> tuple:
    """Extract owner, repo, pr_number from a GitHub PR URL."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        sys.exit(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch PR diff using gh CLI."""
    result = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_number}",
         "-H", "Accept: application/vnd.github.v3.diff"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"Failed to fetch diff: {result.stderr.strip()}")
    return result.stdout


def fetch_pr_meta(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR title and body."""
    result = subprocess.run(
        ["gh", "api", f"repos/{owner}/{repo}/pulls/{pr_number}",
         "--jq", '{title: .title, body: .body}'],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return {"title": "", "body": ""}
    return json.loads(result.stdout)


def get_client() -> anthropic.Anthropic:
    """Create Anthropic client. Uses ANTHROPIC_API_KEY env var by default."""
    return anthropic.Anthropic()


def review_diff(diff: str, meta: dict) -> str:
    """Send diff to Claude and return structured Markdown review."""
    client = get_client()
    prompt = f"""You are a senior code reviewer. Analyze this GitHub PR and produce a structured Markdown review.

PR Title: {meta.get('title', 'N/A')}

Diff:
```
{diff[:MAX_DIFF_CHARS]}
```

Respond with EXACTLY this Markdown structure (no extra sections):

## Summary
(2-3 sentence summary of what this PR does)

## Risks
- (each identified risk as a bullet)

## Suggestions
- (each improvement suggestion as a bullet)

## Confidence
**Score: Low / Medium / High**
(one sentence justification)
"""
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def main():
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Claude PR Review Agent — AI-powered structured PR reviews",
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr)
    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    diff = fetch_diff(owner, repo, pr_number)
    if not diff.strip():
        sys.exit("Empty diff — nothing to review.")

    meta = fetch_pr_meta(owner, repo, pr_number)
    print(f"Reviewing ({len(diff)} chars of diff)...", file=sys.stderr)

    review = review_diff(diff, meta)
    print(review)


if __name__ == "__main__":
    main()
