#!/usr/bin/env python3
"""
claude-review: Claude Code PR review agent

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123 [--model claude-sonnet-4-20250514]
    claude-review --diff ./diff.patch [--output review.md]

Environment:
    ANTHROPIC_API_KEY  - Your Anthropic API key
    GITHUB_TOKEN       - GitHub token for fetching PR diffs (needs repo scope)
"""

import os
import re
import sys
import json
import argparse
import urllib.request
from datetime import datetime

# ─── GitHub ──────────────────────────────────────────────────────────────────

def gh_headers():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_API_TOKEN")
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review/1.0",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def parse_pr_url(url: str):
    """Extract owner, repo, pr_number from GitHub PR URL."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))

def fetch_pr_diff(owner: str, repo: str, pr: int) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr}"
    req = urllib.request.Request(url, headers=gh_headers())
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    return data.get("diff_file_names", []), data

def fetch_pr_with_diff(owner: str, repo: str, pr: int) -> tuple:
    # Get PR info and compare URL
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr}"
    req = urllib.request.Request(url, headers=gh_headers())
    with urllib.request.urlopen(req, timeout=15) as r:
        pr_data = json.loads(r.read())

    # Get the diff
    diff_url = f"https://github.com/{owner}/{repo}/pull/{pr}.diff"
    req2 = urllib.request.Request(diff_url, headers=gh_headers())
    with urllib.request.urlopen(req2, timeout=15) as r:
        diff = r.read().decode("utf-8", errors="ignore")

    return pr_data, diff

# ─── Analysis ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert code reviewer. Analyze the provided PR diff and produce a structured Markdown review.

## Output Format

```markdown
## Summary
[2-3 sentences summarizing what this PR does and why it exists]

## Risks
- **[risk name]**: [brief explanation of the risk]
...

## Improvement Suggestions
- **[suggestion]**: [explanation]
...

## Confidence Score
Low | Medium | High
```

## Guidelines
- Be specific: cite file paths, function names, line numbers
- Flag: security issues, race conditions, missing error handling, untested edge cases
- Acknowledge good patterns too — don't just criticize
- Confidence: High = no blockers, Medium = minor concerns, Low = significant issues found
"""

def analyze_diff(diff: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Send diff to Claude API for analysis."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "## Error\n\nSet `ANTHROPIC_API_KEY` environment variable to use Claude analysis."

    truncated_diff = diff[:15000]  # Safety limit

    payload = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": f"Here is the PR diff to review:\n\n```diff\n{truncated_diff}\n```"
            }
        ]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        method="POST"
    )
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            response = json.loads(r.read())
        return response["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return f"## Error\n\nClaude API error {e.code}: {body[:200]}"
    except Exception as ex:
        return f"## Error\n\n{str(ex)}"

# ─── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="claude-review: Claude Code PR review agent")
    parser.add_argument("--pr", help="GitHub PR URL")
    parser.add_argument("--diff", help="Path to local diff file (or '-' for stdin)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Claude model")
    args = parser.parse_args()

    if args.pr:
        owner, repo, pr_num = parse_pr_url(args.pr)
        pr_data, diff = fetch_pr_with_diff(owner, repo, pr_num)
        title = pr_data.get("title", "")
        meta = f"## PR #{pr_num}: {title}\n\n"
        meta += f"- Repository: {owner}/{repo}\n"
        meta += f"- Author: {pr_data.get('user', {}).get('login', 'unknown')}\n"
        meta += f"- State: {pr_data.get('state', 'unknown')}\n"
        meta += f"- URL: {args.pr}\n\n"
    elif args.diff:
        if args.diff == "-":
            diff = sys.stdin.read()
            meta = "## PR Review (stdin)\n\n"
        else:
            diff = open(args.diff, encoding="utf-8", errors="ignore").read()
            meta = f"## PR Review: {args.diff}\n\n"
    else:
        parser.print_help()
        sys.exit(1)

    review = analyze_diff(diff, model=args.model)
    output = meta + review

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Review written to {args.output}")
    else:
        print(output)

if __name__ == "__main__":
    main()
