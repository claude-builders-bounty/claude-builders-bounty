#!/usr/bin/env python3
"""
Claude Code PR Review Sub-Agent

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

Outputs a structured Markdown review comment with:
- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"


def parse_pr_url(url: str) -> tuple:
    """Parse a PR URL into owner, repo, pr_number."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        print(f"Error: Could not parse PR URL: {url}", file=sys.stderr)
        print("Expected format: https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the PR diff from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR diff: HTTP {e.code} {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error fetching PR diff: {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_metadata(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR title, description, and metadata."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-agent/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR metadata: HTTP {e.code}", file=sys.stderr)
        return {}


def call_claude(prompt: str, system_prompt: str = "") -> str:
    """Call Claude API to analyze the PR diff."""
    if not CLAUDE_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        print("Get your API key at https://console.anthropic.com/", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    messages = [{"role": "user", "content": prompt}]
    if system_prompt:
        body = {
            "model": CLAUDE_MODEL,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages,
        }
    else:
        body = {
            "model": CLAUDE_MODEL,
            "max_tokens": 4096,
            "messages": messages,
        }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(CLAUDE_API_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"Claude API error: HTTP {e.code}", file=sys.stderr)
        if error_body:
            print(error_body[:500], file=sys.stderr)
        sys.exit(1)
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error parsing Claude response: {e}", file=sys.stderr)
        sys.exit(1)


def generate_review(diff: str, metadata: dict) -> str:
    """Generate a structured review using Claude."""
    title = metadata.get("title", "Unknown")
    description = metadata.get("body", "No description provided")
    author = metadata.get("user", {}).get("login", "Unknown")
    changed_files = metadata.get("changed_files", "?")
    additions = metadata.get("additions", "?")
    deletions = metadata.get("deletions", "?")

    system_prompt = """You are a senior software engineer reviewing a pull request.
Provide a structured, honest, and actionable review in Markdown format.

Your review must include these sections:
1. Summary of changes (2-3 sentences)
2. Identified risks (bullet list)
3. Improvement suggestions (bullet list, be specific about file:line)
4. Confidence score: Low / Medium / High

Be constructive. Praise good patterns. Flag real issues. Don't bikeshed.
Output ONLY the review content — no preamble, no signature."""

    prompt = f"""## Pull Request: {title}

**Author:** {author}
**Stats:** {changed_files} files changed, +{additions}/-{deletions}

### Description
{description}

### Diff
```diff
{diff[:15000]}
```

### Instructions
Review the PR above and produce a structured Markdown review with:
1. Summary of changes
2. Identified risks
3. Improvement suggestions
4. Confidence score"""

    return call_claude(prompt, system_prompt)


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Sub-Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
  claude-review --pr https://github.com/owner/repo/pull/123 --verbose
        """,
    )
    parser.add_argument("--pr", required=True, help="PR URL to review")
    parser.add_argument("--output", "-o", help="Save review to file instead of stdout")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show fetch progress")

    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.url if hasattr(args, 'url') else args.pr)

    if args.verbose:
        print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    metadata = fetch_pr_metadata(owner, repo, pr_number)
    diff = fetch_pr_diff(owner, repo, pr_number)

    if not diff:
        print("Error: Empty diff received from GitHub", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        diff_size = len(diff)
        print(f"📄 Diff size: {diff_size:,} bytes", file=sys.stderr)
        print(f"🤖 Reviewing with Claude {CLAUDE_MODEL}...", file=sys.stderr)

    review = generate_review(diff, metadata)

    # Add header
    header = f"""# PR Review: {metadata.get('title', f'#{pr_number}')}

**Repository:** `{owner}/{repo}`
**PR:** [#{pr_number}](https://github.com/{owner}/{repo}/pull/{pr_number})
**Author:** @{metadata.get('user', {}).get('login', 'unknown')}
**Changes:** +{metadata.get('additions', '?')}/-{metadata.get('deletions', '?')} across {metadata.get('changed_files', '?')} files
**Review generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

---
{review}
"""

    if args.output:
        with open(args.output, "w") as f:
            f.write(header)
        if args.verbose:
            print(f"✅ Review saved to {args.output}", file=sys.stderr)
    else:
        print(header)


if __name__ == "__main__":
    main()
