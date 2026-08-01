#!/usr/bin/env python3
"""
claude-review: A CLI tool that takes a GitHub PR URL, fetches the diff,
and returns a structured Markdown review from Claude.

Usage:
    python claude-review.py --pr https://github.com/owner/repo/pull/123
    python claude-review.py --pr owner/repo#123

Output: A structured Markdown review to stdout with:
  - Summary (2-3 sentences)
  - Risks (list)
  - Suggestions (list)
  - Confidence score (Low / Medium / High)

Requires:
    - ANTHROPIC_API_KEY environment variable
    - GITHUB_TOKEN environment variable (for private repos / rate limits)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

# --------- Constants ---------
PR_URL_PATTERN = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)/?$"
)
SHORT_PR_PATTERN = re.compile(
    r"^(?P<owner>[^/]+)/(?P<rep>[^/]+)#(?P<number>\d+)$"
)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
GITHUB_API_URL = "https://api.github.com"
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
MAX_DIFF_CHARS = 100_000  # Truncate huge diffs to avoid API limits


# --------- Helpers ---------
def parse_pr_url(pr: str) -> tuple:
    """Parse a PR reference into (owner, repo, number). Accepts full URL or short form."""
    m = PR_URL_PATTERN.match(pr)
    if m:
        return m["owner"], m["repo"], int(m["number"])
    m = SHORT_PR_PATTERN.match(pr)
    if m:
        return m["owner"], m["rep"], int(m["number"])
    raise ValueError(
        f"Could not parse PR reference: {pr!r}. "
        f"Expected formats: https://github.com/owner/repo/pull/123 OR owner/repo#123"
    )


def fetch_pr_diff(owner: str, repo: str, number: int) -> str:
    """Fetch the raw diff for a PR. Returns the diff text."""
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/pulls/{number}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            pr_data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise SystemExit(f"PR not found: {owner}/{repo}#{number}")
        raise

    # Fetch the diff separately (it's not in the JSON by default)
    diff_url = pr_data.get("diff_url")
    if not diff_url:
        raise SystemExit(f"No diff_url in PR response")

    with urllib.request.urlopen(diff_url, timeout=30) as resp:
        diff = resp.read().decode("utf-8", errors="replace")

    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + f"\n\n[... truncated to {MAX_DIFF_CHARS} chars ...]"

    return diff, pr_data


def build_prompt(diff: str, pr_meta: dict) -> str:
    """Build the Claude prompt."""
    title = pr_meta.get("title", "(no title)")
    body = pr_meta.get("body") or "(no description)"
    return f"""You are reviewing a GitHub Pull Request. Produce a structured Markdown review.

PR Title: {title}
PR Description:
{body[:1000]}

Diff:
```diff
{diff}
```

Produce a review with EXACTLY this structure:

## Summary
<2-3 sentences describing what this PR does>

## Risks
- <risk 1>
- <risk 2>
(or "(no significant risks)" if none)

## Suggestions
- <suggestion 1>
- <suggestion 2>
(or "(no suggestions)" if none)

## Confidence
**Low** | **Medium** | **High** — <one-line justification>

Be specific, reference files/lines from the diff, and focus on real issues not nitpicks.
"""


def call_claude(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Call Claude API and return the review text."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY environment variable is required")

    payload = {
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Claude API error {e.code}: {body}")

    if "content" not in data or not data["content"]:
        raise SystemExit(f"Unexpected Claude response: {data}")
    return data["content"][0]["text"]


# --------- Main ---------
def main():
    parser = argparse.ArgumentParser(
        description="Generate a structured PR review using Claude.",
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub PR URL (https://github.com/owner/repo/pull/123) or short form (owner/repo#123)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    try:
        owner, repo, number = parse_pr_url(args.pr)
    except ValueError as e:
        raise SystemExit(str(e))

    print(f"Fetching PR {owner}/{repo}#{number}...", file=sys.stderr)
    diff, pr_meta = fetch_pr_diff(owner, repo, number)
    print(f"  diff size: {len(diff)} chars", file=sys.stderr)
    print(f"  changed files: {pr_meta.get('changed_files', '?')}", file=sys.stderr)

    print("Calling Claude for review...", file=sys.stderr)
    prompt = build_prompt(diff, pr_meta)
    review_text = call_claude(prompt, args.model)

    if args.output == "json":
        result = {
            "pr": f"{owner}/{repo}#{number}",
            "title": pr_meta.get("title"),
            "review_markdown": review_text,
        }
        print(json.dumps(result, indent=2))
    else:
        print()
        print(review_text)


if __name__ == "__main__":
    main()
