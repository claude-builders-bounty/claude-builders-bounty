#!/usr/bin/env python3
"""Claude Code sub-agent that reviews a PR diff and posts a structured comment.

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --pr https://github.com/owner/repo/pull/123 --post

Environment variables:
    ANTHROPIC_API_KEY  Required. API key used to call Claude.
    GITHUB_TOKEN       Required to read private repos or to post comments with --post.
"""

import argparse
import os
import re
import sys

import requests
import anthropic

REVIEW_PROMPT = """You are a senior software engineer performing a pull request review.
Analyze the following PR diff and produce a structured Markdown review with these exact sections:

## Summary
A 2-3 sentence summary of what the PR changes.

## Risks
- Bullet list of identified risks (security, correctness, performance, etc.)

## Suggestions
- Bullet list of improvement suggestions

## Verdict
One line: Approve / Request Changes / Comment, with a short justification.

PR Title: {title}
PR Description: {body}

Diff:
{diff}
"""

PR_URL_RE = re.compile(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)")


def parse_pr_url(url):
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError(f"Invalid PR URL: {url}")
    owner, repo, number = match.groups()
    return owner, repo, int(number)


def fetch_pr(owner, repo, number, token):
    headers = {"Authorization": f"token {token}"} if token else {}
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"

    resp = requests.get(api_url, headers={**headers, "Accept": "application/vnd.github+json"}, timeout=30)
    resp.raise_for_status()
    pr = resp.json()

    diff_resp = requests.get(api_url, headers={**headers, "Accept": "application/vnd.github.v3.diff"}, timeout=30)
    diff_resp.raise_for_status()
    return pr, diff_resp.text


def truncate_diff(diff, max_chars=60000):
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + "\n\n... (diff truncated) ..."


def generate_review(pr, diff, model):
    client = anthropic.Anthropic()
    prompt = REVIEW_PROMPT.format(
        title=pr.get("title", ""),
        body=pr.get("body") or "(no description)",
        diff=truncate_diff(diff),
    )
    message = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if block.type == "text")


def post_comment(owner, repo, number, token, body):
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    resp = requests.post(api_url, headers=headers, json={"body": body}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR with Claude and print/post a structured review.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--post", action="store_true", help="Post the review as a comment on the PR")
    parser.add_argument("--model", default="claude-sonnet-5", help="Claude model to use")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY environment variable is required")

    github_token = os.environ.get("GITHUB_TOKEN")
    owner, repo, number = parse_pr_url(args.pr)
    pr, diff = fetch_pr(owner, repo, number, github_token)
    review = generate_review(pr, diff, args.model)

    print(review)

