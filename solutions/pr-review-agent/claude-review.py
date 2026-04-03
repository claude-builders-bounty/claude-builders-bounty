#!/usr/bin/env python3
"""
Claude Code PR Review Agent
Uses GitHub API to fetch PR diffs and Claude API to generate structured reviews.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

# ── Constants ────────────────────────────────────────────────────────────────
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-5"
MAX_DIFF_CHARS = 80_000  # truncate very large diffs to stay within context

SYSTEM_PROMPT = """You are an expert software engineer performing a thorough code review.
Given a GitHub pull request diff, produce a structured review in EXACTLY this Markdown format:

### Summary
[2-3 sentences summarising what the PR does and its overall goal]

### Identified Risks
- [risk 1]
- [risk 2]
...

### Improvement Suggestions
- [suggestion 1]
- [suggestion 2]
...

### Confidence Score: [Low|Medium|High]

Rules:
- Summary must be 2-3 sentences, no more.
- List at least 2 risks and at least 2 improvement suggestions.
- Confidence Score must be exactly one of: Low, Medium, High.
  - High   → diff is clear, changes are well-scoped, you have full context.
  - Medium → some context missing or changes are moderate in scope.
  - Low    → very large diff, missing context, or highly complex changes.
- Do NOT include any text outside the four sections above.
- Be specific and actionable. Reference file names and line numbers where possible.
"""


# ── GitHub helpers ────────────────────────────────────────────────────────────

def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    """Extract (owner, repo, pr_number) from a GitHub PR URL."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    m = re.search(pattern, pr_url)
    if not m:
        raise ValueError(f"Cannot parse PR URL: {pr_url}\nExpected format: https://github.com/owner/repo/pull/123")
    return m.group(1), m.group(2), int(m.group(3))


def github_request(url: str, accept: str = "application/vnd.github+json") -> bytes:
    """Make an authenticated (if GH_TOKEN set) request to GitHub."""
    headers = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"GitHub API error {e.code} for {url}: {body}") from e


def fetch_pr_metadata(owner: str, repo: str, pr_number: int) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    data = github_request(url)
    return json.loads(data)


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    raw = github_request(url, accept="application/vnd.github.v3.diff")
    diff = raw.decode(errors="replace")
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n[... diff truncated due to size ...]"
    return diff


# ── Claude helpers ────────────────────────────────────────────────────────────

def call_claude(diff: str, pr_title: str, pr_body: str, model: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set.")

    user_content = f"""PR Title: {pr_title}

PR Description:
{pr_body or '(no description provided)'}

Diff:
```diff
{diff}
```
"""

    payload = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_content}],
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
    }
    req = urllib.request.Request(ANTHROPIC_API_URL, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"Anthropic API error {e.code}: {body}") from e

    return result["content"][0]["text"].strip()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — generates structured Markdown reviews.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  GH_TOKEN=ghp_xxx ANTHROPIC_API_KEY=sk-ant-xxx claude-review --pr https://github.com/django/django/pull/18000
  claude-review --pr https://github.com/owner/repo/pull/123 --model claude-opus-4-5 --output review.md
        """,
    )
    parser.add_argument("--pr", required=True, help="Full GitHub PR URL")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Claude model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--output", help="Write review to this file instead of stdout")
    parser.add_argument("--json", action="store_true", dest="json_out", help="Emit raw JSON response from Anthropic")
    args = parser.parse_args()

    # 1. Parse URL
    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching PR diff for {owner}/{repo}#{pr_number}...", file=sys.stderr)

    # 2. Fetch from GitHub
    try:
        meta = fetch_pr_metadata(owner, repo, pr_number)
        diff = fetch_pr_diff(owner, repo, pr_number)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    pr_title = meta.get("title", "")
    pr_body = meta.get("body", "")
    changed_files = meta.get("changed_files", "?")
    additions = meta.get("additions", "?")
    deletions = meta.get("deletions", "?")

    print(f"Analyzing with Claude ({args.model})...", file=sys.stderr)
    print(f"  Files changed: {changed_files}  +{additions} -{deletions}", file=sys.stderr)

    # 3. Call Claude
    try:
        review = call_claude(diff, pr_title, pr_body, args.model)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Build final output
    header = f"## PR Review: {owner}/{repo}#{pr_number}\n\n"
    full_output = header + review + "\n"

    if args.output:
        with open(args.output, "w") as f:
            f.write(full_output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print()  # blank line after stderr messages
        print(full_output)


if __name__ == "__main__":
    main()
