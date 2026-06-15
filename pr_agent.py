#!/usr/bin/env python3
"""
claude-review — A Claude Code sub-agent that reviews a PR and posts
a structured Markdown comment.

Usage:
    export ANTHROPIC_API_KEY=***
    export GITHUB_TOKEN=***          # optional, for private repos / higher rate limits

    ./pr_agent.py --pr https://github.com/owner/repo/pull/123

Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

# ── Config ─────────────────────────────────────────────────────────────────
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 4096
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
GITHUB_API_URL = "https://api.github.com"


# ── GitHub helpers ─────────────────────────────────────────────────────────


def parse_pr_url(url: str):
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    m = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?].*)?$", url
    )
    if not m:
        print(f"❌ Invalid PR URL: {url}", file=sys.stderr)
        print("   Expected: https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)
    return m.group(1), m.group(2), int(m.group(3))


def github_req(path: str, accept: str | None = None) -> str:
    """Make an authenticated GET request to the GitHub API."""
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "User-Agent": "claude-review-agent",
    }
    if accept:
        headers["Accept"] = accept
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{GITHUB_API_URL}{path}"
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"❌ PR not found at {url}", file=sys.stderr)
            sys.exit(1)
        elif e.code == 403:
            print(f"❌ Rate-limited or forbidden. Try setting GITHUB_TOKEN.", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"❌ GitHub API error {e.code}: {e.read().decode()}", file=sys.stderr)
            sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_metadata(owner: str, repo: str, pr_number: int) -> dict:
    """Fetch PR title, description, and metadata."""
    raw = github_req(f"/repos/{owner}/{repo}/pulls/{pr_number}")
    return json.loads(raw)


def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Fetch the unified diff for a PR."""
    raw = github_req(
        f"/repos/{owner}/{repo}/pulls/{pr_number}",
        accept="application/vnd.github.v3.diff",
    )
    return raw or ""


# ── Claude API ─────────────────────────────────────────────────────────────


def call_claude(prompt: str, system_prompt: str) -> str:
    """Send a prompt to Claude and return the response text."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print(
            "❌ ANTHROPIC_API_KEY environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": CLAUDE_MAX_TOKENS,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    req = urllib.request.Request(
        ANTHROPIC_API_URL, data=payload, headers=headers
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        print(f"❌ Claude API error {e.code}: {err}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ Network error talking to Claude API: {e.reason}", file=sys.stderr)
        sys.exit(1)

    # Extract text from response
    try:
        return "".join(
            block["text"] for block in body["content"] if block["type"] == "text"
        )
    except (KeyError, TypeError):
        print(f"❌ Unexpected Claude API response: {json.dumps(body, indent=2)[:500]}", file=sys.stderr)
        sys.exit(1)


# ── Review logic ───────────────────────────────────────────────────────────


def build_review_prompt(title: str, body: str, diff: str) -> tuple[str, str]:
    """Build system prompt and user prompt for Claude."""

    system = (
        "You are an expert code reviewer. Your task is to analyze a GitHub Pull Request "
        "and produce a structured, actionable code review.\n\n"
        "Output format — use exactly these sections:\n\n"
        "## Summary\n"
        "(2-3 sentences describing what this PR does)\n\n"
        "## Identified Risks\n"
        "- List specific risks, if any\n"
        "- Include security, performance, correctness concerns\n\n"
        "## Improvement Suggestions\n"
        "- Actionable suggestions for improvement\n"
        "- Be specific: mention file names and line numbers where relevant\n\n"
        "## Confidence Score\n"
        "**Low / Medium / High**\n"
        "(How confident are you in this review based on the information available)\n\n"
        "Be thorough but fair. Focus on the diff itself."
    )

    user = f"## Pull Request\n\n**Title:** {title}\n\n"
    if body and body.strip():
        desc = body.strip()[:2000]
        user += f"**Description:**\n{desc}\n\n"
    user += "## Diff\n\n```diff\n"
    diff_truncated = diff[:60000]
    if len(diff) > 60000:
        diff_truncated += "\n# ... (diff truncated due to size)"
    user += diff_truncated
    user += "\n```"

    return system, user


def run_review(pr_url: str):
    """Main review flow."""
    owner, repo, pr_number = parse_pr_url(pr_url)

    print(f"🔍 Fetching PR #{pr_number} from {owner}/{repo}...", file=sys.stderr)

    meta = fetch_pr_metadata(owner, repo, pr_number)
    diff = fetch_pr_diff(owner, repo, pr_number)

    title = meta.get("title", "(no title)")
    body = meta.get("body") or ""

    if not diff:
        print("⚠️  No diff found — PR may be empty or already merged.", file=sys.stderr)
        sys.exit(1)

    diff_kb = len(diff) / 1024
    print(f"📄 Diff size: {diff_kb:.1f} KB", file=sys.stderr)

    print(f"🤖 Sending to Claude ({CLAUDE_MODEL}) for review...", file=sys.stderr)
    system, prompt = build_review_prompt(title, body, diff)
    review = call_claude(prompt, system)

    print()
    print("# Code Review")
    print()
    print(review)


# ── CLI entry point ────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code sub-agent that reviews a GitHub Pull Request.",
    )
    parser.add_argument(
        "--pr", "-p",
        required=True,
        help="GitHub Pull Request URL, e.g. https://github.com/owner/repo/pull/123",
    )
    args = parser.parse_args()

    run_review(args.pr)


if __name__ == "__main__":
    main()
