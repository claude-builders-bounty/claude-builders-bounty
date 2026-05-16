#!/usr/bin/env python3
"""Claude Code PR Reviewer - CBB #4 $150

Usage: claude-review --pr https://github.com/owner/repo/pull/123
   or: python claude_review.py https://github.com/owner/repo/pull/123
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def parse_pr_url(url):
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError("Invalid GitHub PR URL")
    return m.group(1), m.group(2), int(m.group(3))


def api_get(url):
    req = urllib.request.Request(url)
    req.add_header("Authorization", "token " + GITHUB_TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "claude-review/1.0")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print("GitHub API error: {} {}".format(e.code, e.reason), file=sys.stderr)
        sys.exit(1)


def fetch_pr_diff(owner, repo, pr_num):
    url = "https://api.github.com/repos/{}/{}/pulls/{}".format(owner, repo, pr_num)
    pr = api_get(url)
    diff_url = pr.get("diff_url", "")
    if not diff_url:
        sys.exit(1)
    req = urllib.request.Request(diff_url)
    req.add_header("Authorization", "token " + GITHUB_TOKEN)
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "claude-review/1.0")
    with urllib.request.urlopen(req, timeout=30) as resp:
        diff = resp.read().decode("utf-8", errors="replace")
    return diff, pr


def call_claude(prompt):
    data = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=data)
    req.add_header("x-api-key", ANTHROPIC_API_KEY)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode())
    return result["content"][0]["text"]


def generate_review(diff, pr_info):
    prompt = """You are a senior code reviewer. Review this pull request diff and return a structured Markdown review.

## PR Information
- Title: {title}
- Files changed: {files}

## Diff
{diff}

## Instructions
Provide a structured review with these exact sections:

### Summary
2-3 sentences describing what this PR does.

### Identified Risks
Bullet list of potential issues, bugs, or concerns. If none, state "No significant risks identified."

### Improvement Suggestions
Bullet list of specific, actionable suggestions. If none, state "No improvement suggestions."

### Overall Assessment
One of: "Approve", "Approve with Comments", or "Request Changes". Include brief reasoning.

Be specific and reference actual code from the diff. Do not hallucinate.""".format(
        title=pr_info.get("title", "Unknown"),
        files=pr_info.get("changed_files", "?"),
        diff=diff[:8000]
    )
    return call_claude(prompt)


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer")
    parser.add_argument("pr_url", help="GitHub PR URL")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--comment", "-c", action="store_true", help="Post review as PR comment")
    args = parser.parse_args()

    owner, repo, pr_num = parse_pr_url(args.pr_url)

    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    print("Fetching PR diff for {}/{} #{}...".format(owner, repo, pr_num))
    diff, pr_info = fetch_pr_diff(owner, repo, pr_num)

    print("Generating review with Claude...")
    review = generate_review(diff, pr_info)

    full_review = "# PR Review: {} #{}\n\n## {}\n\n{}".format(
        "{}/{}".format(owner, repo), pr_num,
        pr_info.get("title", "PR #{}".format(pr_num)),
        review
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(full_review)
        print("Review saved to {}".format(args.output))
    else:
        print(full_review)

    if args.comment:
        comment_url = "https://api.github.com/repos/{}/{}/issues/{}/comments".format(owner, repo, pr_num)
        data = json.dumps({"body": full_review}).encode()
        req = urllib.request.Request(comment_url, data=data)
        req.add_header("Authorization", "token " + GITHUB_TOKEN)
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "claude-review/1.0")
        req.method = "POST"
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                print("Review posted as PR comment!")
        except urllib.error.HTTPError as e:
            print("Failed to post comment: {} {}".format(e.code, e.reason), file=sys.stderr)


if __name__ == "__main__":
    main()