#!/usr/bin/env python3
"""
claude-review -- AI-powered PR review CLI.

Fetches a GitHub PR diff, analyzes it via Claude API (or OpenAI-compatible),
and outputs a structured Markdown review.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr owner/repo/123
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from typing import Optional


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-20250514"

GITHUB_API_HEADERS = {
    "User-Agent": "claude-review/1.0",
    "Accept": "application/vnd.github.v3.diff",
}


def parse_pr_url(url_or_ref: str) -> tuple[str, str, int]:
    """Parse PR reference: URL or owner/repo/number."""
    url_match = re.match(
        r"(?:https?://)?github\.com/([^/]+)/([^/]+)/pull/(\d+)", url_or_ref
    )
    if url_match:
        return url_match.group(1), url_match.group(2), int(url_match.group(3))
    short_match = re.match(r"([^/]+)/([^/]+)/(\d+)", url_or_ref)
    if short_match:
        return short_match.group(1), short_match.group(2), int(short_match.group(3))
    raise ValueError(f"Cannot parse PR reference: {url_or_ref}")


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> tuple:
    """Fetch PR diff and metadata from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "claude-review/1.0", "Accept": "application/vnd.github.v3+json"},
    )
    with urllib.request.urlopen(req) as resp:
        pr_data = json.loads(resp.read())
    req = urllib.request.Request(url, headers=GITHUB_API_HEADERS)
    with urllib.request.urlopen(req) as resp:
        diff = resp.read().decode("utf-8")
    return diff, pr_data


def build_review_prompt(diff, pr_title, pr_body, files, additions, deletions):
    """Build review prompt for the LLM."""
    body = (pr_body or "No description.")[:500]
    diff_text = diff[:12000]
    return f"""You are a senior software engineer conducting a code review.
Analyze the following GitHub PR diff and produce a structured review.

## PR Context
- Title: {pr_title}
- Files changed: {files}
- Additions: +{additions}
- Deletions: -{deletions}

## PR Description
{body}

## Diff
```diff
{diff_text}
```

## Instructions

Output your review in this exact Markdown format:

```markdown
## Summary
(2-3 sentences describing what this PR does at a high level.)

## Identified Risks
- **Risk**: (specific risk -- omit section if none)

## Improvement Suggestions
- **Suggestion**: (actionable improvement -- omit section if none)

## Confidence Score
High / Medium / Low -- with one-line justification
```

Focus on: logic errors, security issues, performance problems, missing tests,
breaking changes, unclear naming, and edge cases. Do not comment on code style
unless it causes bugs."""


def call_llm(prompt, api_key, model, provider="anthropic"):
    """Call LLM API. Supports 'anthropic' and 'openai'."""
    if provider == "anthropic":
        return _call_anthropic(prompt, api_key, model)
    elif provider == "openai":
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return _call_openai(prompt, api_key, model, base_url)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def _call_anthropic(prompt, api_key, model):
    payload = {"model": model, "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": ANTHROPIC_VERSION},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["content"][0]["text"]


def _call_openai(prompt, api_key, model, base_url):
    payload = {"model": model, "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def review_pr(pr_ref, api_key=None, model=None, provider="anthropic"):
    """Full pipeline: fetch -> analyze -> report."""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No API key. Set ANTHROPIC_API_KEY or OPENAI_API_KEY, or pass --api-key.")
    model = model or DEFAULT_MODEL

    owner, repo, pr_number = parse_pr_url(pr_ref)
    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    diff, pr_data = fetch_pr_diff(owner, repo, pr_number)
    if not diff.strip():
        raise RuntimeError(f"No diff found for PR #{pr_number}.")

    stats = {
        "title": pr_data.get("title", "Unknown"),
        "body": pr_data.get("body", ""),
        "files": pr_data.get("changed_files", 0),
        "additions": pr_data.get("additions", 0),
        "deletions": pr_data.get("deletions", 0),
    }

    print(f"Stats: {stats['files']} files, +{stats['additions']}/-{stats['deletions']}", file=sys.stderr)
    print(f"Analyzing with {provider}/{model}...", file=sys.stderr)

    prompt = build_review_prompt(diff, **stats)
    review = call_llm(prompt, api_key, model, provider)

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    header = (
        f"# PR Review: {stats['title']}\n\n"
        f"**PR**: [{owner}/{repo}#{pr_number}](https://github.com/{owner}/{repo}/pull/{pr_number})\n"
        f"**Reviewed**: {timestamp}\n"
        f"**Stats**: {stats['files']} files changed (+{stats['additions']} -{stats['deletions']})\n\n"
        f"---\n"
    )
    return header + review


def main():
    parser = argparse.ArgumentParser(description="AI-powered GitHub PR review CLI.")
    parser.add_argument("--pr", required=True, help="PR reference: URL or owner/repo/number")
    parser.add_argument("--api-key", default=None, help="API key (or set env var)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
    parser.add_argument("--provider", default="anthropic", choices=["anthropic", "openai"], help="API provider")
    parser.add_argument("--output", "-o", default=None, help="Write review to file")
    args = parser.parse_args()

    try:
        report = review_pr(args.pr, args.api_key, args.model, args.provider)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Review saved to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
