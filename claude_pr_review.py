# Test\nprint("hello")\n#!/usr/bin/env python3
"""
Claude PR Review Agent — CLI tool that analyzes GitHub PR diffs
and generates structured Markdown review comments.

Usage:
  python3 claude_pr_review.py --pr https://github.com/owner/repo/pull/123
  python3 claude_pr_review.py --pr https://github.com/owner/repo/pull/123 --output review.md
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from typing import Optional


def fatal(msg):
    print(f"❌ Error: {msg}", file=sys.stderr)
    sys.exit(1)

def info(msg):
    print(f"ℹ️  {msg}", file=sys.stderr)

def success(msg):
    print(f"✅ {msg}", file=sys.stderr)

def warn(msg):
    print(f"⚠️  {msg}", file=sys.stderr)


def fetch_json(url, token=None):
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-pr-review-agent/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        fatal(f"GitHub API error {e.code}: {body}")
    except Exception as e:
        fatal(f"Network error: {e}")


def fetch_text(url, token=None):
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-pr-review-agent/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        return ""
    except Exception as e:
        fatal(f"Network error: {e}")


def parse_pr_url(url):
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    m = re.match(r'(\d+)', url)
    if m:
        return None, None, int(m.group(1))
    fatal(f"Invalid PR URL: {url}")

def get_github_token():
    for var in ["GITHUB_TOKEN", "GH_TOKEN"]:
        val = os.environ.get(var, "")
        if val and val != "***":
            return val
    return None


def call_claude(prompt, max_tokens=4000):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "***":
        fatal("No ANTHROPIC_API_KEY found in environment.")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode())
            return result["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:1000]
        fatal(f"Claude API error {e.code}: {body}")
    except Exception as e:
        fatal(f"Claude API network error: {e}")

def count_diff_stats(diff):
    files = set()
    additions = 0
    deletions = 0
    for line in diff.split("\n"):
        m = re.match(r'\+\+\+\s+(?:b/)?(.+)', line)
        if m:
            files.add(m.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return {
        "files_changed": len(files),
        "additions": additions,
        "deletions": deletions,
    }


def fetch_pr_data(owner, repo, pr_number, token):
    info(f"Fetching PR #{pr_number} from {owner}/{repo}...")
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    pr_data = fetch_json(pr_url, token)
    diff = fetch_text(pr_url, token)
    if not diff:
        diff = fetch_text(f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff", token)
    stats = count_diff_stats(diff)
    return {
        "title": pr_data.get("title", "Untitled PR"),
        "description": pr_data.get("body", "") or "",
        "author": pr_data.get("user", {}).get("login", "unknown"),
        "base_branch": pr_data.get("base", {}).get("ref", "main"),
        "head_branch": pr_data.get("head", {}).get("ref", "unknown"),
        "diff": diff,
        "stats": stats,
    }

def build_review_prompt(pr_data):
    stats = pr_data["stats"]
    files = re.split(r'(?=diff --git a/)', pr_data["diff"])
    file_sections = []
    for f in files:
        if not f.strip():
            continue
        m = re.search(r'diff --git a/(.+?) b/(.+)', f)
        if m:
            file_sections.append(f"--- {m.group(2)} ---\n{f}")
    file_list = "\n\n".join(file_sections) if file_sections else pr_data["diff"]

    return f"""You are a senior code reviewer. Review this GitHub PR thoroughly.

## PR Metadata
- **Title:** {pr_data['title']}
- **Description:** {pr_data['description'][:2000]}
- **Author:** {pr_data['author']}
- **Branch:** {pr_data['head_branch']} -> {pr_data['base_branch']}
- **Stats:** {stats['files_changed']} files, +{stats['additions']}/-{stats['deletions']} lines

## Review
For each file: what changed, line-level issues, security concerns.
Then overall: Summary, Risks, Suggestions, Quality, Confidence.

## Code Changes
{file_list[:15000]}

## Output: Valid Markdown with Summary, Files table, Risks (HIGH/MEDIUM/LOW), Suggestions (file:line), Quality, Confidence.
"""

def parse_review_output(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r'^```\w*\n', '', raw)
        raw = re.sub(r'\n```$', '', raw)
    return raw


def post_comment(owner, repo, pr_number, comment, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "claude-pr-review-agent/1.0",
        "Content-Type": "application/json",
    }
    body = json.dumps({"body": comment}).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            success(f"Comment posted: {result.get('html_url', '')}")
            return result.get('html_url', '')
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        warn(f"Failed to post comment: {e.code}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Claude PR Review Agent")
    parser.add_argument("--pr", required=True, help="PR URL (https://github.com/owner/repo/pull/123)")
    parser.add_argument("--repo", help="Owner/repo (if --pr is just a number)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--post", action="store_true", help="Post review as PR comment")
    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr)
    if not owner or not repo:
        if not args.repo:
            fatal("--repo is required when --pr is just a number")
        owner, repo = args.repo.split("/", 1)

    token = get_github_token()
    pr_data = fetch_pr_data(owner, repo, pr_number, token)

    info(f"Reviewing: {pr_data['title']}")
    info(f"Changes: {pr_data['stats']['files_changed']} files, +{pr_data['stats']['additions']}/-{pr_data['stats']['deletions']} lines")

    prompt = build_review_prompt(pr_data)
    raw_review = call_claude(prompt)
    review = parse_review_output(raw_review)

    from datetime import datetime
    full_review = f"""# 🤖 Claude PR Review — #{pr_number}

**Repo:** {owner}/{repo}
**PR:** [{pr_data['title']}](https://github.com/{owner}/{repo}/pull/{pr_number})
**Author:** {pr_data['author']}
**Stats:** +{pr_data['stats']['additions']}/-{pr_data['stats']['deletions']} in {pr_data['stats']['files_changed']} files
**Reviewed:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

---

{review}
"""

    if args.output:
        with open(args.output, "w") as f:
            f.write(full_review)
        success(f"Review saved to {args.output}")
    else:
        print(full_review)

    if args.post and token:
        post_comment(owner, repo, pr_number, full_review, token)


if __name__ == "__main__":
    main()
