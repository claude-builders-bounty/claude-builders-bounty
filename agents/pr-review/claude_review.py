#!/usr/bin/env python3
"""
claude-review — A Claude Code agent that reviews GitHub PRs and produces
structured Markdown review comments.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --github-token ghp_xxx
  claude-review --diff diff.patch

Meant to be used with Claude Code or any LLM API as the review engine.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import urllib.request
import urllib.error
from pathlib import Path

VERSION = "1.0.0"

# ── Helpers ──────────────────────────────────────────────────────────────

def fetch_pr_info(pr_url: str, token: str | None = None) -> dict:
    """Fetch PR metadata and diff from GitHub API."""
    # Parse owner/repo/number from URL
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        m = re.match(r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        # Try raw format: owner/repo/pull/123
        m = re.match(r"([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        raise ValueError(f"Could not parse PR URL: {pr_url}\nExpected: https://github.com/owner/repo/pull/123")

    owner, repo, number = m.group(1), m.group(2), m.group(3)

    # Fetch PR metadata (JSON)
    json_headers = {"User-Agent": "claude-review/1.0", "Accept": "application/vnd.github.v3+json"}
    if token:
        json_headers["Authorization"] = f"Bearer {token}"
    pr_url_api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    req = urllib.request.Request(pr_url_api, headers=json_headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            pr_data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API error fetching PR #{number}: {e.code} {e.reason}")

    # Fetch actual diff content
    diff_headers = {"User-Agent": "claude-review/1.0", "Accept": "application/vnd.github.v3.diff"}
    if token:
        diff_headers["Authorization"] = f"Bearer {token}"
    diff_req = urllib.request.Request(pr_url_api, headers=diff_headers)
    try:
        with urllib.request.urlopen(diff_req, timeout=30) as resp:
            diff_content = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API error fetching diff: {e.code} {e.reason}")

    # Fetch PR title and description
    title = pr_data.get("title", "")
    body = pr_data.get("body", "") or ""
    author = pr_data.get("user", {}).get("login", "unknown")
    additions = pr_data.get("additions", 0)
    deletions = pr_data.get("deletions", 0)
    changed_files = pr_data.get("changed_files", 0)
    base_branch = pr_data.get("base", {}).get("ref", "")
    head_branch = pr_data.get("head", {}).get("ref", "")

    return {
        "owner": owner,
        "repo": repo,
        "number": int(number),
        "title": title,
        "body": body,
        "author": author,
        "additions": additions,
        "deletions": deletions,
        "changed_files": changed_files,
        "base_branch": base_branch,
        "head_branch": head_branch,
        "diff": diff_content,
        "url": pr_data.get("html_url", pr_url),
    }


def read_diff_file(path: str) -> str:
    """Read a diff from a local file."""
    with open(path) as f:
        return f.read()


def truncate_diff(diff: str, max_lines: int = 1500) -> str:
    """Truncate very large diffs to avoid token limits."""
    lines = diff.split("\n")
    if len(lines) <= max_lines:
        return diff
    # Keep first max_lines/2 and last max_lines/2
    half = max_lines // 2
    truncated = "\n".join(lines[:half])
    truncated += f"\n\n⋯ [TRUNCATED: {len(lines) - max_lines} lines omitted — showing {half} first + {half} last] ⋯\n\n"
    truncated += "\n".join(lines[-half:])
    return truncated


# ── LLM Review Engine ────────────────────────────────────────────────────

def review_with_api(pr_info: dict, api_key: str | None = None,
                     model: str = "claude-sonnet-4-20250514",
                     base_url: str = "https://api.anthropic.com/v1/messages") -> str:
    """Use Claude API to review the PR diff."""
    diff_text = truncate_diff(pr_info["diff"], 1500)

    diff_summary = (
        f"PR: {pr_info['title']}\n"
        f"Author: {pr_info['author']}\n"
        f"Files changed: {pr_info['changed_files']}\n"
        f"Additions: +{pr_info['additions']}, Deletions: -{pr_info['deletions']}\n"
        f"Base: {pr_info['base_branch']} → Head: {pr_info['head_branch']}\n"
    )

    system_prompt = (
        "You are a world-class code reviewer. Your task is to analyze a GitHub PR diff "
        "and produce a structured review in Markdown format. Be thorough, constructive, "
        "and specific. Focus on correctness, security, performance, and maintainability."
    )

    user_prompt = f"""Please review this GitHub pull request.

{diff_summary}
## Diff
```diff
{diff_text}
```

## PR Description
{pr_info['body'][:1000]}

Please produce a structured review with the following sections:

1. **Summary of Changes** — 2-3 sentences explaining what this PR does
2. **Identified Risks** — numbered list of bugs, security issues, or regressions
3. **Improvement Suggestions** — numbered list of refactoring, performance, or style improvements
4. **Confidence Score** — Low / Medium / High (based on how confident you are in your review)

Focus on problems that would actually cause bugs or security issues in production.
Be constructive: for each issue suggest a specific fix.
"""

    body = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "claude-review/1.0",
        "x-api-key": api_key or "",
        "anthropic-version": "2023-06-01",
    }

    req = urllib.request.Request(base_url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            # Parse Claude API response format
            content = data.get("content", [])
            if isinstance(content, list):
                return "".join(block.get("text", "") for block in content if block.get("type") == "text")
            return str(content)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        raise RuntimeError(f"API error ({e.code}): {error_body[:200]}")
    except Exception as e:
        raise RuntimeError(f"API request failed: {e}")


def review_with_claude_cli(pr_info: dict) -> str:
    """Use the Claude Code CLI (`claude`) to review the PR diff."""
    diff_text = truncate_diff(pr_info["diff"], 2000)

    diff_summary = (
        f"PR: {pr_info['title']}\n"
        f"Author: {pr_info['author']}\n"
        f"Files changed: {pr_info['changed_files']}\n"
        f"Additions: +{pr_info['additions']}, Deletions: -{pr_info['deletions']}\n"
        f"Base: {pr_info['base_branch']} → Head: {pr_info['head_branch']}\n"
    )

    prompt = f"""You are reviewing a GitHub PR. Analyze the diff and produce a structured review.

{diff_summary}
PR Description:
{pr_info['body'][:1000]}

Diff:
```diff
{diff_text}
```

Produce a structured review with:
1. **Summary of Changes**
2. **Identified Risks**
3. **Improvement Suggestions**
4. **Confidence Score** (Low/Medium/High)

Start your response with '## PR Review'."""

    # Try claude CLI
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise RuntimeError(f"claude CLI failed: {result.stderr[:200]}")
    except FileNotFoundError:
        raise RuntimeError(
            "claude CLI not found. Install Claude Code or use --api-key with --api-base-url."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("claude CLI timed out after 120 seconds.")


def review_with_openai_api(pr_info: dict, api_key: str, model: str = "gpt-4o",
                            base_url: str = "https://api.openai.com/v1/chat/completions") -> str:
    """Use OpenAI-compatible API to review the PR diff (works with OpenRouter too)."""
    diff_text = truncate_diff(pr_info["diff"], 1500)

    diff_summary = (
        f"PR: {pr_info['title']}\n"
        f"Author: {pr_info['author']}\n"
        f"Files changed: {pr_info['changed_files']}\n"
        f"Additions: +{pr_info['additions']}, Deletions: -{pr_info['deletions']}\n"
        f"Base: {pr_info['base_branch']} → Head: {pr_info['head_branch']}\n"
    )

    system_prompt = (
        "You are a world-class code reviewer. Analyze GitHub PR diffs and produce "
        "structured Markdown reviews with Summary, Risks, Improvements, and Confidence Score."
    )

    user_prompt = f"""Please review this GitHub pull request.

{diff_summary}
## Diff
```diff
{diff_text}
```

## PR Description
{pr_info['body'][:1000]}

Please produce a structured review with:
1. **Summary of Changes** — 2-3 sentences
2. **Identified Risks** — numbered list
3. **Improvement Suggestions** — numbered list
4. **Confidence Score** — Low / Medium / High"""

    body = json.dumps({
        "model": model,
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "claude-review/1.0",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(base_url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        raise RuntimeError(f"API error ({e.code}): {error_body[:200]}")


def generate_sample_review(pr_info: dict) -> str:
    """Generate a minimal template review when no API is available."""
    return f"""### Summary of Changes
This pull request modifies {pr_info['changed_files']} files with **+{pr_info['additions']}** / **-{pr_info['deletions']}** across `{pr_info['base_branch']}` → `{pr_info['head_branch']}`.

> ⚠️ *Template review. Run with `--api-key`, `--openai-key`, or `--claude` for AI-powered analysis.*

### Identified Risks
1. Review required — unable to assess without AI analysis.

### Improvement Suggestions
1. Review required — unable to assess without AI analysis.

### Confidence Score
**Low** — Review generated from template. Provide an API key for AI-powered analysis.
"""


# ── Output Formatting ────────────────────────────────────────────────────

def format_review(pr_info: dict, review_text: str) -> str:
    """Format the review with a clean header."""
    output = []
    output.append(f"# PR Review: {pr_info['title']}")
    output.append("")
    output.append(f"**PR:** [#{pr_info['number']}]({pr_info['url']})")
    output.append(f"**Author:** `{pr_info['author']}`")
    output.append(f"**Repository:** `{pr_info['owner']}/{pr_info['repo']}`")
    output.append(f"**Files Changed:** {pr_info['changed_files']}  |  **+{pr_info['additions']}** / **-{pr_info['deletions']}**")
    output.append(f"**Branch:** `{pr_info['base_branch']}` → `{pr_info['head_branch']}`")
    output.append("")

    # Remove any leading "# PR Review" from the review text if it already has headers
    review_clean = re.sub(r"^#\s*PR\s*Review.*?\n", "", review_text, count=1, flags=re.IGNORECASE)
    review_clean = review_clean.strip()

    output.append(review_clean)
    output.append("")
    output.append("---")
    output.append(f"*Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) v{VERSION}*")

    return "\n".join(output)


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="claude-review — AI-powered GitHub PR review agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              claude-review --pr https://github.com/owner/repo/pull/123
              claude-review --pr owner/repo/pull/123 --api-key sk-xxx
              claude-review --diff changes.patch --claude
              claude-review --pr https://github.com/owner/repo/pull/123 --openrouter-key sk-or-xxx
        """),
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--pr", help="GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    input_group.add_argument("--diff", help="Path to a local diff/patch file")

    parser.add_argument("--github-token", help="GitHub token for private repos / higher rate limits")
    parser.add_argument("--api-key", help="Anthropic API key for Claude API")
    parser.add_argument("--api-base-url", default="https://api.anthropic.com/v1/messages",
                       help="Anthropic API base URL (default: https://api.anthropic.com/v1/messages)")
    parser.add_argument("--model", default="claude-sonnet-4-20250514",
                       help="Model name (default: claude-sonnet-4-20250514)")
    parser.add_argument("--claude", action="store_true",
                       help="Use Claude Code CLI (`claude`) instead of API")
    parser.add_argument("--openai-key", help="OpenAI-compatible API key (for OpenRouter, etc.)")
    parser.add_argument("--openai-base-url", default="https://api.openai.com/v1/chat/completions",
                       help="OpenAI-compatible base URL")
    parser.add_argument("--openai-model", default="gpt-4o",
                       help="OpenAI-compatible model name")
    parser.add_argument("--openrouter-key", help="OpenRouter API key (shortcut for --openai-key + --openai-base-url)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only output the review, no status messages")
    parser.add_argument("--version", action="version", version=f"claude-review v{VERSION}")

    args = parser.parse_args()

    # ── Handle OpenRouter shortcut ──
    if args.openrouter_key:
        args.openai_key = args.openrouter_key
        args.openai_base_url = "https://openrouter.ai/api/v1/chat/completions"
        if args.openai_model == "gpt-4o":
            args.openai_model = "openai/gpt-4o"  # OpenRouter model format

    # ── Fetch PR info ──
    if not args.quiet:
        print(f"🔍 Fetching PR info...", file=sys.stderr)

    if args.pr:
        try:
            pr_info = fetch_pr_info(args.pr, args.github_token)
        except Exception as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    else:
        pr_info = {
            "diff": read_diff_file(args.diff),
            "title": "Local diff review",
            "author": "unknown",
            "owner": "",
            "repo": "",
            "number": 0,
            "body": "",
            "additions": 0,
            "deletions": 0,
            "changed_files": 0,
            "base_branch": "",
            "head_branch": "",
            "url": args.diff,
        }

    if not args.quiet:
        changes = f"+{pr_info['additions']}/-{pr_info['deletions']} across {pr_info['changed_files']} files"
        print(f"📄 {pr_info['title'][:60]} — {changes}", file=sys.stderr)

    # ── Perform review ──
    if not args.quiet:
        print(f"🤖 Analyzing...", file=sys.stderr)

    if args.claude:
        # Use Claude Code CLI
        try:
            review_text = review_with_claude_cli(pr_info)
        except RuntimeError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    elif args.api_key:
        # Use Anthropic API
        try:
            review_text = review_with_api(pr_info, args.api_key, args.model, args.api_base_url)
        except RuntimeError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    elif args.openai_key:
        # Use OpenAI-compatible API
        try:
            review_text = review_with_openai_api(
                pr_info, args.openai_key, args.openai_model, args.openai_base_url
            )
        except RuntimeError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Fallback with sample review
        review_text = generate_sample_review(pr_info)
        if not args.quiet:
            print(f"⚠️  No API key provided — using template. Pass --api-key, --openai-key, or --claude for AI review.", file=sys.stderr)

    # ── Format and output ──
    formatted = format_review(pr_info, review_text)

    if args.output:
        with open(args.output, "w") as f:
            f.write(formatted)
        if not args.quiet:
            print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(formatted)


if __name__ == "__main__":
    main()
