#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"


def fatal(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def parse_pr_url(url):
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        fatal(f"invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def github_api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github.v3.diff")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        fatal(f"GitHub API error {e.code}: {e.read().decode()}")


def github_api_json(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        fatal(f"GitHub API error {e.code}: {e.read().decode()}")


def fetch_pr_diff(owner, repo, pr_number):
    return github_api(f"/repos/{owner}/{repo}/pulls/{pr_number}")


def fetch_pr_metadata(owner, repo, pr_number):
    data = github_api_json(f"/repos/{owner}/{repo}/pulls/{pr_number}")
    return {
        "title": data.get("title", ""),
        "description": data.get("body", "") or "",
        "author": data.get("user", {}).get("login", ""),
        "base": data.get("base", {}).get("ref", ""),
        "head": data.get("head", {}).get("ref", ""),
        "files_changed": data.get("changed_files", 0),
        "additions": data.get("additions", 0),
        "deletions": data.get("deletions", 0),
    }


def call_claude(diff_text, metadata):
    if not CLAUDE_API_KEY:
        fatal("ANTHROPIC_API_KEY environment variable not set")

    prompt = f"""You are an expert code reviewer. Analyze the following GitHub pull request and produce a structured review.

PR Title: {metadata['title']}
PR Description: {metadata['description']}
Author: @{metadata['author']}
Base: {metadata['base']} <- Head: {metadata['head']}
Files changed: {metadata['files_changed']} ({metadata['additions']} additions, {metadata['deletions']} deletions)

---

DIFF:
```diff
{diff_text[:80000]}
```

---

Produce a structured Markdown review with exactly these sections:

## Summary
2-3 sentences summarizing the changes.

## Identified Risks
- List each risk as a bullet point with a brief explanation.

## Improvement Suggestions
- List each suggestion as a bullet point with a brief explanation.

## Confidence Score
**Confidence: Low / Medium / High**

(A brief 1-sentence justification for the confidence level.)"""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(CLAUDE_API_URL, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-api-key", CLAUDE_API_KEY)
    req.add_header("anthropic-version", "2023-06-01")

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        fatal(f"Claude API error {e.code}: {e.read().decode()}")
    except (KeyError, IndexError) as e:
        fatal(f"unexpected Claude API response: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — analyzes a GitHub PR and produces a structured review."
    )
    parser.add_argument("pr_url", help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")
    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr_url)

    print(f"Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)
    metadata = fetch_pr_metadata(owner, repo, pr_number)
    diff = fetch_pr_diff(owner, repo, pr_number)

    print(f"Analyzing {metadata['files_changed']} files ({metadata['additions']} ++ / {metadata['deletions']} --)...", file=sys.stderr)
    review = call_claude(diff, metadata)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(review)


if __name__ == "__main__":
    main()
