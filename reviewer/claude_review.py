#!/usr/bin/env python3
"""
claude-review — Claude-powered GitHub PR reviewer.
Usage: python claude_review.py --pr https://github.com/owner/repo/pull/123
"""
import argparse
import os
import re
import sys
import httpx
import anthropic

GH_API = "https://api.github.com"


def fetch_pr(pr_url: str, gh_token: str) -> dict:
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url.strip())
    if not m:
        sys.exit(f"Invalid PR URL: {pr_url}")
    owner, repo, number = m.groups()
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {gh_token}",
    }
    pr = httpx.get(f"{GH_API}/repos/{owner}/{repo}/pulls/{number}", headers=headers, timeout=15).json()
    diff_resp = httpx.get(
        f"{GH_API}/repos/{owner}/{repo}/pulls/{number}",
        headers={**headers, "Accept": "application/vnd.github.v3.diff"},
        timeout=15,
    )
    files_resp = httpx.get(f"{GH_API}/repos/{owner}/{repo}/pulls/{number}/files", headers=headers, timeout=15)
    comments_resp = httpx.get(f"{GH_API}/repos/{owner}/{repo}/pulls/{number}/comments", headers=headers, timeout=15)
    return {
        "title": pr.get("title", ""),
        "body": (pr.get("body") or "")[:1000],
        "author": pr.get("user", {}).get("login", "?"),
        "base": pr.get("base", {}).get("ref", ""),
        "head": pr.get("head", {}).get("ref", ""),
        "diff": diff_resp.text[:12000],
        "files": [f["filename"] for f in files_resp.json()] if files_resp.status_code == 200 else [],
        "changed_files": pr.get("changed_files", 0),
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "url": pr_url,
        "comments": len(comments_resp.json()) if comments_resp.status_code == 200 else 0,
    }


def review_pr(pr: dict, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""You are a senior software engineer reviewing a GitHub pull request.

PR: {pr['title']}
Author: {pr['author']}  |  {pr['base']} ← {pr['head']}
Files changed: {pr['changed_files']}  (+{pr['additions']} -{pr['deletions']} lines)
Files: {', '.join(pr['files'][:20])}

PR Description:
{pr['body'] or '(none)'}

Diff (truncated to 12k chars):
```diff
{pr['diff']}
```

Return a structured Markdown review with EXACTLY these sections:

## Summary
2-3 sentences describing what this PR does and its overall quality.

## Identified Risks
- List each risk as a bullet. Include: security issues, breaking changes, missing error handling, race conditions, performance concerns. Write "None identified." if clean.

## Improvement Suggestions
- Specific, actionable improvements. Reference file/line where possible. Write "None." if the code is ready to merge as-is.

## Confidence Score
**[Low / Medium / High]** — one word, bolded, with a one-sentence explanation.
"""
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def main():
    parser = argparse.ArgumentParser(description="Claude-powered GitHub PR reviewer")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--output", default=None, help="Save review to file")
    args = parser.parse_args()

    gh_token = os.getenv("GITHUB_TOKEN", "")
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        sys.exit("Set ANTHROPIC_API_KEY in environment")
    if not gh_token:
        sys.exit("Set GITHUB_TOKEN in environment")

    print(f"Fetching PR: {args.pr}")
    pr = fetch_pr(args.pr, gh_token)
    print(f"Reviewing: {pr['title']} (+{pr['additions']} -{pr['deletions']})")

    review = review_pr(pr, api_key)
    header = f"# PR Review: {pr['title']}\n\n**URL:** {pr['url']}  \n**Author:** @{pr['author']}  \n**Changes:** +{pr['additions']} -{pr['deletions']} across {pr['changed_files']} file(s)\n\n---\n\n"
    output = header + review

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review saved to {args.output}")
    else:
        print("\n" + output)


if __name__ == "__main__":
    main()
