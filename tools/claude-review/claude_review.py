#!/usr/bin/env python3
"""
claude-review — Claude Code PR review sub-agent

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

Requires:
    - ANTHROPIC_API_KEY env var
    - GITHUB_TOKEN env var (for private repos or --post-comment)
"""

import argparse
import json
import os
import re
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError


# ── Claude API ────────────────────────────────────────────────────────────────

CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

REVIEW_PROMPT = """\
You are an expert code reviewer with deep knowledge of software engineering best practices, \
security, and clean code principles. You have been given the diff of a GitHub Pull Request.

Analyze the diff thoroughly and return a structured review in **exactly** the following Markdown format:

---

## 📋 Summary of Changes

<2–3 sentences explaining what this PR does and its overall scope.>

---

## ⚠️ Identified Risks

<Bullet list of potential bugs, security issues, performance concerns, or breaking changes. \
If none, write "- No significant risks identified.">

---

## 💡 Improvement Suggestions

<Bullet list of concrete code quality suggestions, naming improvements, missing tests, \
documentation gaps, etc. If none, write "- Code looks good as-is.">

---

## 🎯 Confidence Score

**<Low | Medium | High>** — <One sentence explaining why this confidence level was chosen \
based on the scope and complexity of the diff.>

---

Here is the PR diff to review:

```diff
{diff}
```
"""


def call_claude(prompt: str, api_key: str) -> str:
    """Call the Claude API and return the text response."""
    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = Request(
        CLAUDE_API_URL,
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(req) as resp:
            body = json.loads(resp.read().decode())
            return body["content"][0]["text"]
    except HTTPError as e:
        error_body = e.read().decode()
        raise RuntimeError(f"Claude API error {e.code}: {error_body}") from e


# ── GitHub API ────────────────────────────────────────────────────────────────

def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    """Parse owner, repo, PR number from a GitHub PR URL."""
    match = re.match(
        r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$", pr_url.strip()
    )
    if not match:
        raise ValueError(
            f"Invalid PR URL: {pr_url!r}\n"
            "Expected format: https://github.com/owner/repo/pull/123"
        )
    return match.group(1), match.group(2), int(match.group(3))


def github_request(path: str, token: str | None = None, accept: str = "application/vnd.github+json") -> dict | str:
    """Make a GitHub API request."""
    url = f"https://api.github.com{path}"
    headers = {
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read().decode()
            if "json" in content_type:
                return json.loads(raw)
            return raw
    except HTTPError as e:
        raise RuntimeError(f"GitHub API error {e.code} on {path}: {e.read().decode()}") from e


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: str | None) -> str:
    """Fetch the unified diff for a PR."""
    diff = github_request(
        f"/repos/{owner}/{repo}/pulls/{pr_number}",
        token=token,
        accept="application/vnd.github.v3.diff",
    )
    if not isinstance(diff, str) or not diff.strip():
        raise RuntimeError("No diff returned for this PR (it may be empty or a merge commit).")
    return diff


def post_pr_comment(owner: str, repo: str, pr_number: int, body: str, token: str) -> str:
    """Post a review comment to a PR."""
    payload = json.dumps({"body": body}).encode()
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    req = Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "claude-review/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(req) as resp:
            result = json.loads(resp.read().decode())
            return result.get("html_url", "")
    except HTTPError as e:
        raise RuntimeError(f"Failed to post comment: {e.read().decode()}") from e


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR reviewer — generates a structured review comment using AI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/42
  claude-review --pr https://github.com/owner/repo/pull/42 --post-comment
  claude-review --pr https://github.com/owner/repo/pull/42 --output review.md
        """,
    )
    parser.add_argument("--pr", required=True, metavar="URL", help="GitHub PR URL to review")
    parser.add_argument(
        "--post-comment", action="store_true",
        help="Post the review as a GitHub comment (requires GITHUB_TOKEN)"
    )
    parser.add_argument("--output", metavar="FILE", help="Save review to a Markdown file")
    args = parser.parse_args()

    # Validate environment
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    github_token = os.environ.get("GITHUB_TOKEN", "").strip() or None
    if args.post_comment and not github_token:
        print("ERROR: --post-comment requires GITHUB_TOKEN to be set.", file=sys.stderr)
        sys.exit(1)

    # Parse PR URL
    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Fetching diff for {owner}/{repo}#{pr_number}...")
    try:
        diff = fetch_pr_diff(owner, repo, pr_number, github_token)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Truncate very large diffs to avoid token limits
    max_diff_chars = 24_000
    if len(diff) > max_diff_chars:
        diff = diff[:max_diff_chars] + "\n\n[... diff truncated for length ...]"

    print(f"🤖 Calling Claude ({CLAUDE_MODEL})...")
    prompt = REVIEW_PROMPT.format(diff=diff)
    try:
        review = call_claude(prompt, api_key)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    header = f"> 🤖 **Automated PR Review** — generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty) using `{CLAUDE_MODEL}`\n\n"
    full_review = header + review

    # Output
    print("\n" + "=" * 60)
    print(full_review)
    print("=" * 60 + "\n")

    if args.output:
        with open(args.output, "w") as f:
            f.write(full_review)
        print(f"✅ Review saved to {args.output}")

    if args.post_comment:
        print(f"💬 Posting comment to {args.pr}...")
        try:
            comment_url = post_pr_comment(owner, repo, pr_number, full_review, github_token)
            print(f"✅ Comment posted: {comment_url}")
        except RuntimeError as e:
            print(f"ERROR posting comment: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
