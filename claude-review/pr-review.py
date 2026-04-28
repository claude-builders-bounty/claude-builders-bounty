#!/usr/bin/env python3
"""
PR Review Agent — a CLI tool that reviews GitHub PRs using Claude API.
Zero external dependencies: uses only Python stdlib.

Usage:
  python3 pr-review.py --pr https://github.com/owner/repo/pull/123

Bounty: $150 — powered by Opire (https://opire.dev)
"""

import argparse
import json
import os
import re
import sys
import urllib.request


ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"


def parse_args():
    parser = argparse.ArgumentParser(description="Review a GitHub PR using Claude API")
    parser.add_argument("--pr", required=True, help="Full GitHub PR URL")
    parser.add_argument("-o", "--output", help="Save output to file")
    parser.add_argument("--custom-instructions", help="Extra context for the review")
    parser.add_argument("--github-token", help="GitHub token (default: GITHUB_TOKEN env var)")
    return parser.parse_args()


def _parse_pr_url(url: str) -> tuple:
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        sys.exit(f"Error: invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def _gh_headers_json(token: str | None) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "claude-pr-review-agent/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch(url: str, headers: dict) -> str:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fetch_pr_diff(owner: str, repo: str, pr_num: int, token: str | None) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    headers = {"Accept": "application/vnd.github.v3.diff", "User-Agent": "claude-pr-review-agent/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return _fetch(url, headers)


def fetch_pr_metadata(owner: str, repo: str, pr_num: int, token: str | None) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    return json.loads(_fetch(url, _gh_headers_json(token)))


def call_claude(prompt: str, api_key: str) -> str:
    body = json.dumps({"model": CLAUDE_MODEL, "max_tokens": 4096, "messages": [{"role": "user", "content": prompt}]}).encode()
    headers = {"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"}
    req = urllib.request.Request(ANTHROPIC_API, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode())
    content = result.get("content", [])
    return "".join(block.get("text", "") for block in content) if content else "Error: no content"


def build_review_prompt(title: str, body: str, diff: str, instructions: str | None) -> str:
    prompt = f"""You are a code review agent. Review this PR and produce structured Markdown.

## PR Title
{title}

## PR Description
{body or '(no description)'}

## Diff
{diff[-20000:]}

"""
    if instructions:
        prompt += f"\n## Additional Instructions\n{instructions}\n"
    prompt += """

Format your review exactly:

## Summary
(2-3 sentences)

### Identified Risks
- risk 1

### Improvement Suggestions
1. suggestion 1

### Confidence Score
**High** / Medium / Low
"""
    return prompt


def main():
    args = parse_args()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Error: ANTHROPIC_API_KEY not set")
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    owner, repo, pr_num = _parse_pr_url(args.pr)
    print(f"Fetching PR #{pr_num} from {owner}/{repo}...", file=sys.stderr)
    try:
        metadata = fetch_pr_metadata(owner, repo, pr_num, github_token)
        diff = fetch_pr_diff(owner, repo, pr_num, github_token)
    except Exception as e:
        sys.exit(f"Error fetching PR: {e}")
    title = metadata.get("title", "")
    body = metadata.get("body", "")
    print("Analyzing with Claude...", file=sys.stderr)
    prompt = build_review_prompt(title, body, diff, args.custom_instructions)
    try:
        review = call_claude(prompt, api_key)
    except Exception as e:
        sys.exit(f"Error calling Claude: {e}")
    output = f"# PR Review: {owner}/{repo}#{pr_num}\n\n**PR:** {args.pr}\n**Title:** {title}\n\n---\n\n{review}\n"
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review saved to {args.output}")
    else:
        print(f"\n{output}")


if __name__ == "__main__":
    main()
