#!/usr/bin/env python3
"""Claude-powered PR reviewer — structured analysis via Claude API."""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


def fetch(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API error {e.code}: {e.reason} — {url}")


def fetch_text(url: str, accept: str) -> str:
    req = urllib.request.Request(url, headers={"Accept": accept})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API error {e.code}: {e.reason}")


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        sys.exit(f"Invalid PR URL: {url}\nExpected: https://github.com/owner/repo/pull/N")
    return m.group(1), m.group(2), int(m.group(3))


def get_pr_data(owner: str, repo: str, pr_num: int, gh_token: str | None) -> dict:
    headers: dict = {"Accept": "application/vnd.github+json"}
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"

    api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    pr = fetch(api, headers)

    diff_headers = dict(headers)
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    diff = fetch_text(api, diff_headers["Accept"])

    files_data = fetch(f"{api}/files", headers)
    file_names = [f["filename"] for f in files_data[:20]]

    return {
        "title": pr["title"],
        "author": pr["user"]["login"],
        "base": pr["base"]["ref"],
        "head": pr["head"]["ref"],
        "body": pr.get("body") or "(no description)",
        "additions": pr["additions"],
        "deletions": pr["deletions"],
        "files": file_names,
        "diff": diff[:12000],  # keep under token limit
    }


def build_prompt(pr: dict) -> str:
    return f"""You are a senior software engineer doing a pull request review.

PR title: {pr['title']}
Author: {pr['author']}
Base ← Head: {pr['base']} ← {pr['head']}
Additions: +{pr['additions']}  Deletions: -{pr['deletions']}
Files changed: {', '.join(pr['files'])}

Description:
{pr['body']}

Diff (truncated to 12 000 chars):
```diff
{pr['diff']}
```

Produce ONLY the following structured Markdown — no preamble:

## Summary
(2–3 sentences describing what this PR does and why)

## Identified Risks
- (list each risk; write "None identified" if clean)

## Improvement Suggestions
- (actionable suggestions; write "None" if none)

## Confidence Score
(one of: Low | Medium | High — based on diff clarity, test coverage, and scope)
"""


def call_claude(prompt: str, api_key: str, model: str) -> str:
    payload = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        sys.exit(f"Anthropic API error {e.code}: {body}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review a GitHub PR with Claude.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example:\n  claude-review --pr https://github.com/owner/repo/pull/42",
    )
    parser.add_argument("--pr", required=True, metavar="URL", help="GitHub PR URL")
    parser.add_argument(
        "--model",
        default="claude-haiku-4-5-20251001",
        metavar="MODEL",
        help="Claude model ID (default: claude-haiku-4-5-20251001)",
    )
    parser.add_argument("--output", metavar="FILE", help="Write output to FILE instead of stdout")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Error: ANTHROPIC_API_KEY environment variable is not set.")

    gh_token = os.environ.get("GITHUB_TOKEN")

    owner, repo, pr_num = parse_pr_url(args.pr)
    print(f"Fetching PR #{pr_num} from {owner}/{repo}…", file=sys.stderr)
    pr_data = get_pr_data(owner, repo, pr_num, gh_token)

    print(f"Reviewing with {args.model}…", file=sys.stderr)
    prompt = build_prompt(pr_data)
    review = call_claude(prompt, api_key, args.model)

    header = f"# PR Review: {pr_data['title']}\n\n> {args.pr}\n\n"
    output = header + review

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
