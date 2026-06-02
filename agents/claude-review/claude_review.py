#!/usr/bin/env python3
"""
claude-review — Claude Code PR Review Sub-Agent

Accepts a GitHub PR URL, fetches the diff via `gh CLI`,
sends it to Claude for analysis, and outputs a structured
Markdown review comment.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
    claude-review --pr https://github.com/owner/repo/pull/123 --post
    claude-review --diff ./local.diff

Environment:
    ANTHROPIC_API_KEY  — required for Claude API access
    GITHUB_TOKEN       — optional, for private repos and --post
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── Constants ──────────────────────────────────────────────────────────────────

MODEL = "claude-sonnet-4-20250514"
MAX_DIFF_CHARS = 200_000  # Truncate very large diffs

REVIEW_SYSTEM_PROMPT = """\
You are an expert code reviewer. Analyze the following PR diff and produce a \
structured Markdown review. You MUST follow this exact format:

## 📋 Change Summary
(2–3 sentences summarizing what the PR does)

## ⚠️ Identified Risks
- (List each risk as a bullet point; if none, write "None identified")

## 💡 Improvement Suggestions
- (List each suggestion as a bullet point; if none, write "None")

## 🏆 Code Quality Score: X/10
(Provide a single integer 1–10 with a brief 1-line justification)

Do NOT output anything outside this structure. Be concise but precise. \
Focus on correctness, security, maintainability, and style.
"""

# ── Helpers ────────────────────────────────────────────────────────────────────


def _run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _parse_pr_url(url: str) -> tuple[str, str, str]:
    """
    Parse a GitHub PR URL into (owner, repo, pr_number).

    Supports:
      https://github.com/owner/repo/pull/123
      https://github.com/owner/repo/pull/123/files
    """
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    m = re.search(pattern, url)
    if not m:
        raise ValueError(f"Cannot parse PR URL: {url}")
    return m.group(1), m.group(2), m.group(3)


def fetch_pr_diff(owner: str, repo: str, pr_number: str) -> str:
    """Fetch the diff for a PR using `gh api`."""
    endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}"
    try:
        result = _run_cmd(["gh", "api", endpoint, "-H", "Accept: application/vnd.github.v3.diff"])
    except subprocess.CalledProcessError as exc:
        print(f"❌ Failed to fetch PR diff: {exc.stderr}", file=sys.stderr)
        sys.exit(1)
    diff = result.stdout
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n... [diff truncated for size]"
    return diff


def fetch_pr_metadata(owner: str, repo: str, pr_number: str) -> dict:
    """Fetch PR title, author, and stats via gh api."""
    endpoint = f"repos/{owner}/{repo}/pulls/{pr_number}"
    try:
        result = _run_cmd(["gh", "api", endpoint])
        data = json.loads(result.stdout)
        return {
            "title": data.get("title", "Unknown"),
            "author": data.get("user", {}).get("login", "unknown"),
            "additions": data.get("additions", 0),
            "deletions": data.get("deletions", 0),
            "changed_files": data.get("changed_files", 0),
            "url": data.get("html_url", ""),
        }
    except Exception:
        return {"title": "Unknown", "author": "unknown", "additions": 0, "deletions": 0, "changed_files": 0, "url": ""}


def read_local_diff(path: str) -> str:
    """Read a diff from a local file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Diff file not found: {path}")
    diff = p.read_text(encoding="utf-8", errors="replace")
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n... [diff truncated for size]"
    return diff


def call_claude(diff: str, metadata: Optional[dict] = None) -> str:
    """
    Send the diff to Claude API and return the review text.

    Uses the `anthropic` Python SDK if available, otherwise falls back
    to a direct HTTP request via `curl`.
    """
    # Build the user message
    parts = []
    if metadata:
        parts.append(
            f"PR: {metadata.get('title', 'Unknown')}\n"
            f"Author: {metadata.get('author', 'unknown')}\n"
            f"Changes: +{metadata.get('additions', 0)} / -{metadata.get('deletions', 0)} "
            f"({metadata.get('changed_files', 0)} files)"
        )
    parts.append(f"```diff\n{diff}\n```")
    user_message = "\n\n".join(parts)

    # Try anthropic SDK first
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is required")

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=REVIEW_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    except ImportError:
        # Fall back to curl
        pass

    # Curl fallback
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)

    payload = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 2048,
            "system": REVIEW_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_message}],
        }
    )

    try:
        result = _run_cmd(
            [
                "curl", "-sS", "https://api.anthropic.com/v1/messages",
                "-H", f"x-api-key: {api_key}",
                "-H", "anthropic-version: 2023-06-01",
                "-H", "content-type: application/json",
                "-d", payload,
            ]
        )
        data = json.loads(result.stdout)
        if "content" in data:
            return data["content"][0]["text"]
        elif "error" in data:
            print(f"❌ Claude API error: {data['error']}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"❌ Unexpected API response: {result.stdout[:500]}", file=sys.stderr)
            sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"❌ curl failed: {exc.stderr}", file=sys.stderr)
        sys.exit(1)


def post_review_comment(owner: str, repo: str, pr_number: str, body: str) -> None:
    """Post the review as a PR comment using gh api."""
    endpoint = f"repos/{owner}/{repo}/issues/{pr_number}/comments"
    payload = json.dumps({"body": body})
    try:
        _run_cmd(
            [
                "gh", "api", endpoint,
                "-X", "POST",
                "-H", "Accept: application/vnd.github.v3+json",
                "-f", f"body={body}",
            ]
        )
        print(f"✅ Review comment posted to PR #{pr_number}")
    except subprocess.CalledProcessError as exc:
        print(f"❌ Failed to post comment: {exc.stderr}", file=sys.stderr)
        sys.exit(1)


# ── CLI ────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Claude Code sub-agent that reviews a PR and outputs structured Markdown.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--pr",
        help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)",
    )
    group.add_argument(
        "--diff",
        help="Path to a local .diff or .patch file",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write review to this file instead of stdout",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post the review as a comment on the PR (requires --pr)",
    )
    parser.add_argument(
        "--model",
        default=MODEL,
        help=f"Claude model to use (default: {MODEL})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output review as JSON instead of Markdown",
    )
    return parser


def main() -> None:
    global MODEL

    parser = build_parser()
    args = parser.parse_args()

    if args.model:
        MODEL = args.model

    # ── Fetch diff ────────────────────────────────────────────────────────
    metadata = None

    if args.pr:
        try:
            owner, repo, pr_number = _parse_pr_url(args.pr)
        except ValueError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)

        print(f"🔍 Fetching diff for {owner}/{repo}#{pr_number}...", file=sys.stderr)
        diff = fetch_pr_diff(owner, repo, pr_number)
        metadata = fetch_pr_metadata(owner, repo, pr_number)
        metadata["pr_number"] = pr_number

    elif args.diff:
        print(f"🔍 Reading diff from {args.diff}...", file=sys.stderr)
        try:
            diff = read_local_diff(args.diff)
        except FileNotFoundError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
        owner = repo = pr_number = None

    if not diff.strip():
        print("❌ Empty diff — nothing to review.", file=sys.stderr)
        sys.exit(1)

    # ── Call Claude ────────────────────────────────────────────────────────
    print(f"🤖 Sending to Claude ({MODEL})...", file=sys.stderr)
    review_text = call_claude(diff, metadata)

    # Add header with PR info
    if metadata:
        header = (
            f"## 🤖 Automated PR Review — {owner}/{repo}#{pr_number}\n\n"
            f"**PR:** [{metadata['title']}]({metadata['url']})\n"
            f"**Author:** @{metadata['author']} | "
            f"**Changes:** +{metadata['additions']} / -{metadata['deletions']} "
            f"({metadata['changed_files']} files)\n"
            f"**Model:** {MODEL}\n\n---\n\n"
        )
        review_text = header + review_text

    # ── Output ─────────────────────────────────────────────────────────────
    if args.json_output:
        output = json.dumps(
            {
                "pr": args.pr,
                "model": MODEL,
                "review": review_text,
                "metadata": metadata,
            },
            indent=2,
            ensure_ascii=False,
        )
    else:
        output = review_text

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(output)

    # ── Post (optional) ────────────────────────────────────────────────────
    if args.post and owner and repo and pr_number:
        print("📤 Posting review comment...", file=sys.stderr)
        post_review_comment(owner, repo, pr_number, review_text)


if __name__ == "__main__":
    main()
