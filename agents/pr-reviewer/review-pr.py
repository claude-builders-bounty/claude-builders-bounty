#!/usr/bin/env python3
"""
Claude Code Sub-Agent: PR Reviewer
Fetches a GitHub pull request, reviews it using Claude API,
and posts a structured review comment back to GitHub.

Usage:
    python review-pr.py <owner> <repo> <pr_number>

Environment variables required:
    ANTHROPIC_API_KEY   — Claude API key
    GITHUB_TOKEN        — GitHub personal access token (needs repo + PR write access)
"""

import json
import os
import sys
import textwrap
from typing import Any

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_DIFF_CHARS = 40_000  # truncate very large diffs to stay within context limits


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def gh_request(method: str, url: str, body: dict | None = None) -> Any:
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
        "User-Agent": "claude-pr-reviewer/1.0",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        raise RuntimeError(f"GitHub API error {e.code}: {body_text}") from e


def fetch_pr(owner: str, repo: str, pr_number: int) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    return gh_request("GET", url)


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    token = os.environ.get("GITHUB_TOKEN", "")
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.diff",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "claude-pr-reviewer/1.0",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_pr_files(owner: str, repo: str, pr_number: int) -> list[dict]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    return gh_request("GET", url)


def post_comment(owner: str, repo: str, pr_number: int, body: str) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    return gh_request("POST", url, {"body": body})


# ---------------------------------------------------------------------------
# Claude helpers
# ---------------------------------------------------------------------------

def call_claude(prompt: str) -> str:
    import urllib.request, urllib.error
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
        return result["content"][0]["text"]


# ---------------------------------------------------------------------------
# Review logic
# ---------------------------------------------------------------------------

REVIEW_PROMPT_TEMPLATE = """\
You are a senior software engineer performing a structured code review of a GitHub pull request.

## Pull Request

**Title**: {title}
**Author**: {author}
**Base branch**: {base} ← {head}
**Description**:
{body}

## Changed Files

{file_summary}

## Diff (truncated to {diff_chars} chars if large)

```diff
{diff}
```

---

Please write a structured PR review with the following sections. Be specific, cite line numbers or file names where relevant, and keep feedback constructive and actionable.

## 📋 Summary
One paragraph overview of what this PR does and your overall impression.

## ✅ Strengths
What's done well. Be specific.

## 🔍 Issues & Suggestions
List each issue with:
- **Severity**: 🔴 Critical / 🟡 Important / 🔵 Minor
- **File/Line**: where it occurs
- **Issue**: what the problem is
- **Suggestion**: how to fix it

## 🧪 Testing
Observations about test coverage. Is it sufficient? What's missing?

## 🚦 Verdict
One of: **✅ Approve** / **🔄 Request Changes** / **💬 Comment only**

Brief justification for your verdict.
"""


def build_file_summary(files: list[dict]) -> str:
    lines = []
    for f in files[:30]:  # cap at 30 files
        status = f.get("status", "?")
        additions = f.get("additions", 0)
        deletions = f.get("deletions", 0)
        lines.append(f"  {status:8s} +{additions}/-{deletions}  {f['filename']}")
    if len(files) > 30:
        lines.append(f"  … and {len(files) - 30} more files")
    return "\n".join(lines)


def review_pr(owner: str, repo: str, pr_number: int) -> None:
    print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}…")
    pr = fetch_pr(owner, repo, pr_number)
    files = fetch_pr_files(owner, repo, pr_number)
    diff = fetch_pr_diff(owner, repo, pr_number)

    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n[… diff truncated for context limit …]"

    prompt = REVIEW_PROMPT_TEMPLATE.format(
        title=pr["title"],
        author=pr["user"]["login"],
        base=pr["base"]["ref"],
        head=pr["head"]["ref"],
        body=pr.get("body") or "_No description provided._",
        file_summary=build_file_summary(files),
        diff_chars=MAX_DIFF_CHARS,
        diff=diff,
    )

    print("🤖 Asking Claude to review…")
    review_text = call_claude(prompt)

    comment_body = textwrap.dedent(f"""\
        ## 🤖 Automated PR Review — powered by Claude

        > Generated by [claude-pr-reviewer](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) using `{CLAUDE_MODEL}`.

        ---

        {review_text}

        ---
        *This review is AI-generated. A human reviewer should verify findings before merging.*
    """)

    print("💬 Posting review comment to GitHub…")
    result = post_comment(owner, repo, pr_number, comment_body)
    print(f"✅ Review posted: {result['html_url']}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: python review-pr.py <owner> <repo> <pr_number>", file=sys.stderr)
        sys.exit(1)

    owner, repo, pr_number_str = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        pr_number = int(pr_number_str)
    except ValueError:
        print(f"Error: pr_number must be an integer, got {pr_number_str!r}", file=sys.stderr)
        sys.exit(1)

    missing = [v for v in ("ANTHROPIC_API_KEY", "GITHUB_TOKEN") if not os.environ.get(v)]
    if missing:
        print(f"Error: missing environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    review_pr(owner, repo, pr_number)


if __name__ == "__main__":
    main()
