#!/usr/bin/env python3
"""
claude-review — PR reviewer powered by Claude API

Usage:
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123
    python3 claude-review.py --pr owner/repo/123
    python3 claude-review.py --pr owner/repo/123 --post-comment
    python3 claude-review.py --pr owner/repo/123 --json

Requirements:
    - ANTHROPIC_API_KEY env var
    - GITHUB_TOKEN env var (or gh CLI authenticated)

Zero dependencies — stdlib only.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone


# ──────────────────────────────────────────────────────────────────────────────
# GitHub helpers
# ──────────────────────────────────────────────────────────────────────────────

def parse_pr_url(pr_ref: str) -> tuple[str, str, int]:
    """Return (owner, repo, pr_number) from a URL or 'owner/repo/123' string."""
    pr_ref = pr_ref.strip().rstrip("/")
    if pr_ref.startswith("http"):
        # https://github.com/owner/repo/pull/123
        parts = pr_ref.replace("https://github.com/", "").split("/")
        return parts[0], parts[1], int(parts[3])
    # owner/repo/123  or  owner/repo#123
    pr_ref = pr_ref.replace("#", "/")
    parts = pr_ref.split("/")
    return parts[0], parts[1], int(parts[2])


def github_get(path: str, token: str | None = None) -> dict | list:
    url = f"https://api.github.com{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def github_post_comment(owner: str, repo: str, pr_number: int, body: str, token: str) -> str:
    """Post a review comment on a PR. Returns the comment URL."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "claude-review/1.0",
    }
    data = json.dumps({"body": body}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
        return result["html_url"]


def fetch_pr_data(owner: str, repo: str, pr_number: int, token: str | None) -> dict:
    """Fetch PR metadata, diff, and files changed."""
    pr = github_get(f"/repos/{owner}/{repo}/pulls/{pr_number}", token)

    # Fetch diff (up to 100 KB)
    diff_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.diff",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(diff_url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        diff = resp.read().decode(errors="replace")

    # Truncate very large diffs
    MAX_DIFF_CHARS = 80_000
    truncated = False
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS]
        truncated = True

    # Files changed
    files = github_get(f"/repos/{owner}/{repo}/pulls/{pr_number}/files", token)

    return {
        "title": pr["title"],
        "body": pr.get("body") or "",
        "author": pr["user"]["login"],
        "base": pr["base"]["ref"],
        "head": pr["head"]["ref"],
        "additions": pr["additions"],
        "deletions": pr["deletions"],
        "changed_files": pr["changed_files"],
        "diff": diff,
        "diff_truncated": truncated,
        "files": [f["filename"] for f in files],
        "url": pr["html_url"],
        "created_at": pr["created_at"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# Claude API
# ──────────────────────────────────────────────────────────────────────────────

def call_claude(prompt: str, api_key: str, model: str = "claude-sonnet-4-20250514") -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Claude API error {e.code}: {body}") from e


# ──────────────────────────────────────────────────────────────────────────────
# Review logic
# ──────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a senior software engineer performing a thorough code review.
Analyze the PR diff and produce a structured Markdown review with these exact sections:

## Summary
2-3 sentences describing what this PR does and why.

## Identified Risks
A bulleted list of risks (security, correctness, performance, maintainability).
If none, write "No significant risks identified."

## Improvement Suggestions
A numbered list of actionable suggestions (code quality, missing tests, naming, etc.).
Be specific — reference file names and line patterns where possible.
If none, write "No further improvements needed."

## Confidence Score
One of: **Low** / **Medium** / **High** — followed by a one-sentence rationale.

Keep the review concise and actionable. Do not repeat the diff verbatim.
"""


def build_prompt(pr: dict) -> str:
    files_list = "\n".join(f"  - {f}" for f in pr["files"])
    trunc_note = "\n[DIFF TRUNCATED at 80 KB — large PR]" if pr["diff_truncated"] else ""
    return f"""{SYSTEM_PROMPT}

---

**PR:** {pr['url']}
**Title:** {pr['title']}
**Author:** @{pr['author']}
**Base → Head:** {pr['base']} → {pr['head']}
**Stats:** +{pr['additions']} / -{pr['deletions']} across {pr['changed_files']} files

**Files changed:**
{files_list}

**PR description:**
{pr['body'][:2000] if pr['body'] else '(no description)'}

**Diff:**
```diff
{pr['diff']}{trunc_note}
```
"""


def format_review(pr: dict, review_text: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""# PR Review: {pr['title']}

> **Repository:** `{pr['url'].split('github.com/')[1].rsplit('/pull', 1)[0]}`
> **PR:** {pr['url']}
> **Author:** @{pr['author']} | **Base → Head:** `{pr['base']}` → `{pr['head']}`
> **Stats:** +{pr['additions']} deletions -{pr['deletions']} across {pr['changed_files']} file(s)
> **Reviewed at:** {now} by claude-review

---

{review_text}

---

*Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty/tree/main/submissions/issue-4-pr-reviewer) — powered by Anthropic Claude*
"""


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Review a GitHub PR using Claude API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 claude-review.py --pr https://github.com/owner/repo/pull/123
  python3 claude-review.py --pr owner/repo/123
  python3 claude-review.py --pr owner/repo/123 --post-comment
  python3 claude-review.py --pr owner/repo/123 --json > review.json
        """,
    )
    parser.add_argument("--pr", required=True, help="PR URL or owner/repo/number")
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the review as a GitHub comment (requires GITHUB_TOKEN with write access)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of Markdown",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Anthropic model ID (default: claude-sonnet-4-20250514)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    github_token = os.environ.get("GITHUB_TOKEN")

    # Parse PR ref
    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except (IndexError, ValueError) as e:
        print(f"ERROR: Could not parse PR reference '{args.pr}': {e}", file=sys.stderr)
        print("Expected: https://github.com/owner/repo/pull/123 or owner/repo/123", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching PR {owner}/{repo}#{pr_number} ...", file=sys.stderr)
    pr_data = fetch_pr_data(owner, repo, pr_number, github_token)

    print(f"Calling Claude ({args.model}) ...", file=sys.stderr)
    prompt = build_prompt(pr_data)
    review_text = call_claude(prompt, api_key, args.model)
    full_review = format_review(pr_data, review_text)

    if args.json:
        output = {
            "pr_url": pr_data["url"],
            "pr_title": pr_data["title"],
            "author": pr_data["author"],
            "stats": {
                "additions": pr_data["additions"],
                "deletions": pr_data["deletions"],
                "changed_files": pr_data["changed_files"],
            },
            "review_markdown": full_review,
            "model": args.model,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }
        print(json.dumps(output, indent=2))
    else:
        print(full_review)

    if args.post_comment:
        if not github_token:
            print("ERROR: GITHUB_TOKEN required to post comments", file=sys.stderr)
            sys.exit(1)
        comment_url = github_post_comment(owner, repo, pr_number, full_review, github_token)
        print(f"\nReview posted: {comment_url}", file=sys.stderr)


if __name__ == "__main__":
    main()
