#!/usr/bin/env python3
"""
PR Review Agent — Claude Code Sub-Agent

Analyzes a PR diff and returns a structured Markdown review comment.

Usage:
    python pr_reviewer.py --pr https://github.com/owner/repo/pull/123
    python pr_reviewer.py --diff diff.patch
    python pr_reviewer.py --pr <url> --output review.md
    python pr_reviewer.py --pr <url> --post-comment
"""

import argparse
import json
import os
import re
import sys
import subprocess
from pathlib import Path
from urllib.parse import urlparse

# --- API Clients ---


def call_openai_compatible(prompt: str, diff: str) -> str:
    """Call any OpenAI-compatible API (Bailian, OpenAI, etc.)."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Installing openai...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai", "-q"])
        from openai import OpenAI

    base_url = os.environ.get("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model = os.environ.get("OPENAI_MODEL", "qwen3.6-plus")

    if not api_key:
        raise SystemExit("Error: OPENAI_API_KEY not set")

    client = OpenAI(base_url=base_url, api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{prompt}\n\n```\n{diff}\n```"},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def call_anthropic(prompt: str, diff: str) -> str:
    """Call Anthropic Claude API."""
    try:
        import anthropic
    except ImportError:
        print("Installing anthropic...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "anthropic", "-q"])
        import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    if not api_key:
        raise SystemExit("Error: ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=0.3,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"{prompt}\n\n```\n{diff}\n```"},
        ],
    )
    return response.content[0].text


# --- Prompt ---

SYSTEM_PROMPT = """You are an expert code reviewer. Analyze the provided PR diff and produce a structured Markdown review.

Rules:
- Be specific, reference actual code changes from the diff
- Focus on correctness, security, performance, and maintainability
- Don't nitpick on style issues unless they affect functionality
- If the diff is large, focus on the most impactful changes
- Output ONLY the review in the format below, no preamble"""

REVIEW_PROMPT = """Review this pull request diff and provide your analysis.

Use the following Markdown structure exactly:

## 📋 PR Review

### Summary
2-3 sentences summarizing what this PR changes and why.

### ⚠️ Identified Risks
- **Category** — Specific risk with reference to the changed code
(Include "No significant risks identified" if none)

### 💡 Improvement Suggestions
- **Type** — Actionable suggestion with code reference
(Include "No improvements suggested — looks solid" if none)

### 🎯 Confidence Score
**High | Medium | Low** — Brief explanation of why"""


# --- Diff Fetching ---


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse GitHub PR URL → (owner, repo, pr_number)."""
    # Handle both https://github.com/owner/repo/pull/123 and short forms
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_diff_from_github(owner: str, repo: str, pr_number: int, token: str | None = None) -> str:
    """Fetch PR diff via GitHub REST API."""
    import urllib.request

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def fetch_diff_cli(pr_url: str) -> str:
    """Fetch PR diff using gh CLI if available."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", pr_url, "--json", "diffUrl"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            diff_url = data.get("diffUrl", "")
            if diff_url:
                import urllib.request
                with urllib.request.urlopen(diff_url, timeout=30) as resp:
                    return resp.read().decode("utf-8")
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # Fallback: REST API
    owner, repo, num = parse_pr_url(pr_url)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    return fetch_diff_from_github(owner, repo, num, token)


def fetch_diff_from_file(path: str) -> str:
    """Read diff from a local file."""
    return Path(path).read_text(encoding="utf-8")


# --- GitHub Comment Posting ---


def post_github_comment(pr_url: str, comment: str, token: str | None = None) -> bool:
    """Post a review comment to the PR via GitHub API."""
    import urllib.request

    owner, repo, pr_number = parse_pr_url(pr_url)
    github_token = token or os.environ.get("GITHUB_TOKEN")

    if not github_token:
        # Try gh CLI
        try:
            result = subprocess.run(
                ["gh", "pr", "comment", pr_url, "--body", comment],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                print(f"✅ Comment posted via gh CLI", file=sys.stderr)
                return True
            else:
                print(f"❌ gh CLI failed: {result.stderr}", file=sys.stderr)
                return False
        except FileNotFoundError:
            print("Error: GITHUB_TOKEN not set and gh CLI not found", file=sys.stderr)
            return False

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    payload = json.dumps({"body": comment}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 201:
                print(f"✅ Comment posted to {pr_url}", file=sys.stderr)
                return True
    except Exception as e:
        print(f"❌ Failed to post comment: {e}", file=sys.stderr)
        return False
    return False


# --- Main ---


def main():
    parser = argparse.ArgumentParser(description="PR Review Agent — structured PR analysis")
    parser.add_argument("--pr", "--pr-url", dest="pr_url", help="GitHub PR URL")
    parser.add_argument("--diff", help="Path to diff file")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--post-comment", action="store_true", help="Post review as PR comment")
    parser.add_argument("--token", help="GitHub API token")
    parser.add_argument("--model", help="Model override (e.g., claude-sonnet-4-20250514)")

    args = parser.parse_args()

    if not args.pr_url and not args.diff:
        parser.print_help()
        sys.exit(1)

    # Fetch diff
    print("Fetching diff...", file=sys.stderr)
    if args.diff:
        diff_text = fetch_diff_from_file(args.diff)
    else:
        diff_text = fetch_diff_cli(args.pr_url)

    if not diff_text or len(diff_text.strip()) < 10:
        print("Error: Could not fetch diff", file=sys.stderr)
        sys.exit(1)

    print(f"Diff size: {len(diff_text)} chars", file=sys.stderr)

    # Call LLM
    print("Analyzing PR...", file=sys.stderr)
    if os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        review = call_anthropic(REVIEW_PROMPT, diff_text)
    else:
        review = call_openai_compatible(REVIEW_PROMPT, diff_text)

    # Output
    if args.output:
        Path(args.output).write_text(review, encoding="utf-8")
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(review)

    # Post comment if requested
    if args.post_comment and args.pr_url:
        post_github_comment(args.pr_url, review, args.token)


if __name__ == "__main__":
    main()
