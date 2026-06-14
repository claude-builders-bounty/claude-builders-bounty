#!/usr/bin/env python3
"""
claude-review — Analyze a GitHub PR diff and return structured markdown feedback.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --post
  GITHUB_TOKEN=ghp_... ANTHROPIC_API_KEY=sk-... claude-review --pr URL
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


def parse_pr_url(url):
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), m.group(3)


def github_api(path, token=None):
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"GitHub API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def github_api_json(path, token=None):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"GitHub API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def post_comment(owner, repo, pr_number, body, token):
    data = json.dumps({"body": body}).encode("utf-8")
    path = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "claude-review/1.0",
    }
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Failed to post comment: {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def call_claude(prompt, api_key, model="claude-sonnet-4-20250514"):
    data = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read().decode("utf-8"))
            return resp["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Claude API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def truncate_diff(diff, max_lines=200):
    lines = diff.split("\n")
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n\n... (truncated, {len(lines) - max_lines} more lines)"
    return diff


def get_pr_metadata(owner, repo, pr_number, token):
    data = github_api_json(f"/repos/{owner}/{repo}/pulls/{pr_number}", token)
    return {
        "title": data.get("title", ""),
        "description": data.get("body", ""),
        "author": data.get("user", {}).get("login", "unknown"),
        "base_branch": data.get("base", {}).get("ref", ""),
        "head_branch": data.get("head", {}).get("ref", ""),
        "changed_files": data.get("changed_files", 0),
        "additions": data.get("additions", 0),
        "deletions": data.get("deletions", 0),
    }


def generate_review(diff, metadata):
    diff_excerpt = truncate_diff(diff)

    prompt = f"""You are a senior engineer reviewing a pull request. Analyze the diff below and produce structured feedback.

## PR Metadata
- Title: {metadata['title']}
- Author: {metadata['author']}
- Base: {metadata['base_branch']} ← Head: {metadata['head_branch']}
- Files changed: {metadata['changed_files']}
- Additions: {metadata['additions']}  Deletions: {metadata['deletions']}

## Diff
```diff
{diff_excerpt}
```

## Instructions
Produce a structured review in markdown with these sections:

### Summary
2-3 sentences describing what this PR does.

### Identified Risks
List specific risks, if any. Consider: security, performance, data loss, breaking changes, concurrency issues. Use "- risk: explanation" format. If no significant risks, write "None identified."

### Improvement Suggestions
Specific, actionable suggestions. Use "- suggestion: explanation" format. Include line numbers when relevant.

### Confidence Score
**High** / **Medium** / **Low** — based on how confident you are in this review.

Focus on real issues. Do not nitpick formatting or style unless it causes functional problems."""

    return prompt


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a GitHub PR diff and return structured feedback."
    )
    parser.add_argument("--pr", required=True, help="PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--post", action="store_true", help="Post review as PR comment")
    parser.add_argument("--model", default="claude-sonnet-4-20250514", help="Claude model")
    args = parser.parse_args()

    gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    claude_key = os.environ.get("ANTHROPIC_API_KEY")

    if not gh_token:
        print("Warning: GITHUB_TOKEN not set. API rate limits will be low.", file=sys.stderr)
    if not claude_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    owner, repo, pr_number = parse_pr_url(args.pr)

    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
    metadata = get_pr_metadata(owner, repo, pr_number, gh_token)
    diff = github_api(f"/repos/{owner}/{repo}/pulls/{pr_number}", gh_token)

    if not diff:
        print("Error: Empty diff received.", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing {metadata['changed_files']} files ({metadata['additions']}+ / {metadata['deletions']}-)...", file=sys.stderr)
    prompt = generate_review(diff, metadata)

    print("Calling Claude API...", file=sys.stderr)
    review = call_claude(prompt, claude_key, args.model)

    output = f"## 🤖 Claude Review: {metadata['title']}\n\n{review}"

    if args.post:
        if not gh_token:
            print("Error: GITHUB_TOKEN required to post comments.", file=sys.stderr)
            sys.exit(1)
        print("Posting review comment...", file=sys.stderr)
        result = post_comment(owner, repo, pr_number, output, gh_token)
        print(f"✅ Review posted: {result.get('html_url', '')}")
    else:
        print(output)


if __name__ == "__main__":
    main()
