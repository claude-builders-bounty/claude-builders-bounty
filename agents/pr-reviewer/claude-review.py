#!/usr/bin/env python3
"""
claude-review: A CLI tool that uses Claude to analyze GitHub PRs and produce
structured review comments.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr owner/repo/123
    claude-review --diff-file changes.diff
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path


CLAUDE_MODEL = "claude-sonnet-4-20250514"

REVIEW_SYSTEM_PROMPT = """You are an expert code reviewer. Analyze the provided PR diff and produce a structured review.

You MUST respond with valid JSON in exactly this format:
{
  "summary": "2-3 sentence summary of what this PR does and why.",
  "risks": [
    "Risk 1: description",
    "Risk 2: description"
  ],
  "suggestions": [
    "Suggestion 1: description",
    "Suggestion 2: description"
  ],
  "confidence": "Low|Medium|High"
}

Rules:
- summary: 2-3 sentences covering WHAT changed and WHY
- risks: potential bugs, security issues, breaking changes, performance concerns. Can be empty [] if none found.
- suggestions: concrete improvements. Can be empty [] if the PR looks good.
- confidence: Low if the diff is unclear/incomplete, Medium if reasonable analysis possible, High if clear and thorough review done
- Be specific. Reference file names and line changes.
- Do NOT include anything outside the JSON object."""


def parse_pr_url(pr_url: str) -> tuple:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    # Handle full URL
    patterns = [
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)",
        r"([^/]+)/([^/]+)/(\d+)",
        r"([^/]+)/([^/]+)/pull/(\d+)",
    ]
    for pattern in patterns:
        m = re.match(pattern, pr_url.strip().rstrip("/"))
        if m:
            return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(f"Cannot parse PR URL: {pr_url}")


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the diff of a GitHub PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-bot",
    }
    gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: PR not found: {owner}/{repo}#{pr_number}", file=sys.stderr)
        elif e.code == 403:
            print("Error: Rate limited or unauthorized. Set GITHUB_TOKEN.", file=sys.stderr)
        else:
            print(f"Error fetching PR: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_info(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR metadata (title, body, etc.)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-bot",
    }
    gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError:
        return {}


def call_claude(diff: str, pr_info: dict = None) -> dict:
    """Call Claude API to review the diff."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable required.", file=sys.stderr)
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...", file=sys.stderr)
        sys.exit(1)

    # Truncate very large diffs to fit context
    max_diff_chars = 150_000
    truncated = False
    if len(diff) > max_diff_chars:
        diff = diff[:max_diff_chars]
        truncated = True

    user_message = f"Review this PR diff:\n\n```diff\n{diff}\n```"
    if truncated:
        user_message += "\n\n[NOTE: Diff was truncated due to size. Review based on available content.]"

    if pr_info:
        title = pr_info.get("title", "")
        body = pr_info.get("body", "")[:500]
        user_message = f"PR Title: {title}\nPR Description: {body}\n\n{user_message}"

    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1024,
        "system": REVIEW_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_message}],
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            text = result["content"][0]["text"]
            # Parse JSON from response, handling possible markdown fences
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*\n?", "", text)
                text = re.sub(r"\n?```\s*$", "", text)
            return json.loads(text)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"Error calling Claude API: HTTP {e.code}", file=sys.stderr)
        print(f"Response: {body[:500]}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Claude returned invalid JSON. Raw response:", file=sys.stderr)
        print(text[:1000], file=sys.stderr)
        sys.exit(1)


def format_markdown(review: dict, pr_url: str = None) -> str:
    """Format the review as Markdown."""
    lines = []
    if pr_url:
        lines.append(f"## 🔍 PR Review: {pr_url}\n")
    else:
        lines.append("## 🔍 PR Review\n")

    lines.append(f"**Confidence:** {review.get('confidence', 'N/A')}\n")
    lines.append(f"### Summary\n{review.get('summary', 'No summary provided.')}\n")

    risks = review.get("risks", [])
    lines.append("### ⚠️ Identified Risks")
    if risks:
        for r in risks:
            lines.append(f"- {r}")
    else:
        lines.append("- None identified")
    lines.append("")

    suggestions = review.get("suggestions", [])
    lines.append("### 💡 Suggestions")
    if suggestions:
        for s in suggestions:
            lines.append(f"- {s}")
    else:
        lines.append("- Looks good! No suggestions.")
    lines.append("")

    lines.append("---\n*Reviewed by claude-review using Claude*")
    return "\n".join(lines)


def post_github_comment(owner: str, repo: str, pr_number: int, body: str):
    """Post a comment on a GitHub PR."""
    gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not gh_token:
        print("Warning: No GITHUB_TOKEN. Printing review to stdout instead.", file=sys.stderr)
        print(body)
        return

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-bot",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print(f"✅ Review posted: {result.get('html_url', 'success')}")
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"Error posting comment: HTTP {e.code}", file=sys.stderr)
        print(body_text[:500], file=sys.stderr)
        print("\nReview output:\n", file=sys.stderr)
        print(body)


def main():
    parser = argparse.ArgumentParser(
        description="Review GitHub PRs using Claude AI"
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub PR URL or owner/repo/number format",
    )
    parser.add_argument(
        "--diff-file",
        help="Use a local diff file instead of fetching from GitHub",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        default=True,
        help="Post review as a GitHub comment (default: true if GITHUB_TOKEN set)",
    )
    parser.add_argument(
        "--no-post",
        action="store_true",
        help="Only print review, don't post to GitHub",
    )
    parser.add_argument(
        "--output",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr)
    pr_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}"

    print(f"Fetching PR: {owner}/{repo}#{pr_number}...", file=sys.stderr)

    if args.diff_file:
        with open(args.diff_file) as f:
            diff = f.read()
        pr_info = {}
    else:
        diff = fetch_pr_diff(owner, repo, pr_number)
        pr_info = fetch_pr_info(owner, repo, pr_number)

    print(f"Diff size: {len(diff)} chars", file=sys.stderr)
    print("Analyzing with Claude...", file=sys.stderr)

    review = call_claude(diff, pr_info)

    if args.output == "json":
        output = json.dumps(review, indent=2)
    else:
        output = format_markdown(review, pr_url)

    if args.no_post:
        print(output)
    else:
        post_github_comment(owner, repo, pr_number, output)
        if not (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")):
            print(output)


if __name__ == "__main__":
    main()
