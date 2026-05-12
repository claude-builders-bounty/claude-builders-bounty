#!/usr/bin/env python3
"""Claude Code sub-agent that reviews PRs and posts structured comments."""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ANTHROPIC_VERSION = "2023-06-01"
CLAUDE_MODEL = "claude-sonnet-4-20250514"


def parse_pr_url(url):
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    m = re.search(pattern, url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_pr_diff(owner, repo, pr_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR #{pr_number}: {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_metadata(owner, repo, pr_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-agent",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR metadata: {e.code} {e.reason}", file=sys.stderr)
        return {}


def call_claude(diff, pr_meta):
    repo_name = pr_meta.get("base", {}).get("repo", {}).get("full_name", "unknown/repo")
    pr_title = pr_meta.get("title", "Untitled PR")
    pr_body = (pr_meta.get("body") or "")[:2000]

    prompt = f"""You are a code review assistant. Analyze the following pull request and provide a structured review.

Repository: {repo_name}
PR Title: {pr_title}
PR Description: {pr_body}

Diff:
```diff
{diff[:80000]}
```

Provide your review in the following format:

## Summary
(2-3 sentence summary of the changes)

## Identified Risks
- (risk 1)
- (risk 2)
- ...

## Improvement Suggestions
- (suggestion 1)
- (suggestion 2)
- ...

## Confidence Score
High / Medium / Low
"""

    body = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("content", [{}])[0].get("text", "")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Claude API error: {e.code}\n{body}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR using Claude")
    parser.add_argument("--pr", required=True, help="PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr)
    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    pr_meta = fetch_pr_metadata(owner, repo, pr_number)
    diff = fetch_pr_diff(owner, repo, pr_number)

    if not diff:
        print("No diff content found — PR may be empty or inaccessible.", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing diff ({len(diff)} bytes)...", file=sys.stderr)
    review = call_claude(diff, pr_meta)

    header = f"""# PR Review: {pr_meta.get('title', f'PR #{pr_number}')}

**Repository:** {owner}/{repo}
**PR:** #{pr_number}
**URL:** {args.pr}
**Review generated:** Claude {CLAUDE_MODEL}

---
"""
    output = header + review

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
