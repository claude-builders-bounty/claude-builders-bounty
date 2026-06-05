#!/usr/bin/env python3
"""
claude-review — PR Reviewer powered by Claude.

A CLI tool that fetches a GitHub PR diff and uses Anthropic's Claude API to
produce a structured Markdown review with:
  - Summary of changes (2–3 sentences)
  - Identified risks
  - Improvement suggestions
  - Confidence score (Low / Medium / High)

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

REVIEW_PROMPT = """You are an expert code reviewer. Analyze the following PR diff and produce a structured Markdown review.

Your output MUST follow this exact format — do not add extra sections or deviate:

## Summary
2–3 sentences explaining what the PR does and why.

## Identified Risks
- Risk 1: description
- Risk 2: description

## Improvement Suggestions
- Suggestion 1: description
- Suggestion 2: description

## Confidence Score
**High / Medium / Low**

The confidence score reflects how certain you are of your assessment:
- **High**: The diff is clean, well-structured, and you're confident in your recommendations.
- **Medium**: There are some concerns but you need more context to be fully sure.
- **Low**: The diff is complex, lacks context, or has significant issues that need deeper investigation.

Here is the PR diff:

```diff
{diff}
```
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    # Support optional trailing slash and http/https (or bare github.com)
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$"
    m = re.search(pattern, url)
    if not m:
        raise ValueError(f"Invalid GitHub PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str | None = None) -> str:
    """Fetch the diff of a GitHub PR via the public API.

    Uses an unauthenticated request when no token is provided (subject to
    GitHub's rate limit of ~60 req/h for unauthenticated clients).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            diff = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"GitHub API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)

    if not diff.strip():
        print("Empty diff received — is the PR URL correct?", file=sys.stderr)
        sys.exit(1)

    return diff


def call_claude(api_key: str, diff: str, model: str = CLAUDE_MODEL) -> str:
    """Send the diff to Claude and return the review text."""
    payload = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": REVIEW_PROMPT.replace("{diff}", diff),
            }
        ],
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "User-Agent": "claude-review/1.0",
    }

    req = urllib.request.Request(
        ANTHROPIC_API_URL, data=payload, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Anthropic API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)

    # Parse response — handle different message content shapes
    content_blocks = result.get("content", [])
    text_parts = []
    for block in content_blocks:
        if isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(block.get("text", ""))
        elif isinstance(block, str):
            text_parts.append(block)

    return "\n".join(text_parts)


def build_metadata_header(
    owner: str, repo: str, pr_number: int, model: str,
) -> str:
    """Build a front-matter / header block explaining what this is."""
    pr_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}"
    return (
        f"<!-- Auto-generated by claude-review -->\n"
        f"**PR:** [{owner}/{repo}#{pr_number}]({pr_url})\n"
        f"**Model:** {model}\n"
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n\n"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Review a GitHub PR using Claude.",
        epilog="Example: claude-review --pr https://github.com/owner/repo/pull/123",
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="Full GitHub PR URL, e.g. https://github.com/owner/repo/pull/123",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Write review to this file instead of stdout",
    )
    parser.add_argument(
        "--model",
        default=CLAUDE_MODEL,
        help=f"Anthropic model to use (default: {CLAUDE_MODEL})",
    )
    parser.add_argument(
        "--github-token",
        default=None,
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Skip the metadata header in output (useful for CI pipelines)",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()

    # Resolve API keys ----------------------------------------------------------
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print(
            "Error: ANTHROPIC_API_KEY environment variable is not set.\n"
            "Export it before running:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "Or set it in your .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")

    # Parse & fetch -----------------------------------------------------------
    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Fetching PR {owner}/{repo}#{pr_number} ...", file=sys.stderr)
    diff = fetch_pr_diff(owner, repo, pr_number, token=github_token)
    print(f"📄 Diff size: {len(diff):,} bytes ({diff.count(chr(10))} lines)", file=sys.stderr)

    # Review ------------------------------------------------------------------
    print(f"🤖 Reviewing with {args.model} ...", file=sys.stderr)
    review = call_claude(anthropic_key, diff, model=args.model)

    # Compose output ----------------------------------------------------------
    output = ""
    if not args.no_header:
        output += build_metadata_header(owner, repo, pr_number, args.model)
    output += review.strip() + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
