#!/usr/bin/env python3
"""
claude-review — AI-powered PR review using Claude.

Produces structured Markdown reviews with summary, risks, suggestions,
and a confidence score. Works as a CLI tool and as a GitHub Action.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr owner/repo/123 --focus security,performance
    claude-review --pr owner/repo/123 --format json

Environment:
    ANTHROPIC_API_KEY  — Required. Your Anthropic API key.
    GITHUB_TOKEN       — Optional. For private repos or higher rate limits.
    CLAUDE_MODEL       — Optional. Model to use (default: claude-sonnet-4-5).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ── Constants ──────────────────────────────────────────────────────────────────

DEFAULT_MODEL = "claude-sonnet-4-5"
MAX_DIFF_CHARS = 100_000  # Truncate diffs beyond this to stay within context
MAX_FILES_IN_DETAIL = 30  # Show per-file details for up to N files
ANTHROPIC_VERSION = "2023-06-01"
USER_AGENT = "claude-review/1.0"

REVIEW_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a senior software engineer performing a code review.
    You are thorough but practical — you flag real issues, not nitpicks.

    Your review MUST follow this exact Markdown structure:

    ## Summary of Changes
    (2-3 sentences describing what this PR does and why)

    ## Identified Risks
    (Bullet list of potential bugs, security issues, breaking changes, or regressions.
    If none, write "No significant risks identified.")

    ## Improvement Suggestions
    (Bullet list of concrete, actionable improvements.
    If none, write "No suggestions — this looks good.")

    ## Confidence Score
    **High** / **Medium** / **Low** — based on:
    - High: Changes are straightforward, well-tested, low risk
    - Medium: Some concerns but nothing blocking
    - Low: Significant risks or insufficient context to assess

    Rules:
    - Be specific. Reference file names and line numbers when possible.
    - Don't repeat what the code already does well unless it's notable.
    - Focus on: correctness, security, performance, maintainability.
    - Ignore: formatting, naming preferences, style unless they cause bugs.
    - If the diff is truncated, note what you couldn't review.
""")


# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class PRInfo:
    owner: str
    repo: str
    number: int
    title: str = ""
    description: str = ""
    author: str = ""
    base_branch: str = ""
    head_branch: str = ""
    state: str = ""
    url: str = ""


@dataclass
class ReviewResult:
    pr: PRInfo
    markdown: str
    model: str
    diff_chars: int
    files_changed: int
    truncated: bool
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


# ── GitHub API ─────────────────────────────────────────────────────────────────

class GitHubClient:
    """Minimal GitHub API client using stdlib only."""

    API = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token

    def _request(self, url: str, accept: str = "application/vnd.github+json") -> bytes:
        req = urllib.request.Request(url)
        req.add_header("Accept", accept)
        req.add_header("User-Agent", USER_AGENT)
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        if self.token:
            req.add_header("Authorization", f"token {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code == 404:
                raise SystemExit(f"PR not found: {url}\nCheck the URL and GITHUB_TOKEN.")
            if e.code == 403:
                raise SystemExit(f"GitHub API rate limited or forbidden.\nSet GITHUB_TOKEN for higher limits.\n{body[:200]}")
            raise SystemExit(f"GitHub API error {e.code}: {body[:300]}")

    def get_json(self, url: str) -> dict:
        return json.loads(self._request(url))

    def get_text(self, url: str, accept: str) -> str:
        return self._request(url, accept).decode("utf-8", errors="replace")

    def get_pr_info(self, owner: str, repo: str, number: int) -> PRInfo:
        data = self.get_json(f"{self.API}/repos/{owner}/{repo}/pulls/{number}")
        return PRInfo(
            owner=owner,
            repo=repo,
            number=number,
            title=data.get("title", ""),
            description=(data.get("body") or "")[:500],
            author=data.get("user", {}).get("login", ""),
            base_branch=data.get("base", {}).get("ref", ""),
            head_branch=data.get("head", {}).get("ref", ""),
            state=data.get("state", ""),
            url=data.get("html_url", ""),
        )

    def get_pr_diff(self, owner: str, repo: str, number: int) -> str:
        return self.get_text(
            f"{self.API}/repos/{owner}/{repo}/pulls/{number}",
            accept="application/vnd.github.diff",
        )

    def get_pr_files(self, owner: str, repo: str, number: int) -> list[dict]:
        data = self.get_json(f"{self.API}/repos/{owner}/{repo}/pulls/{number}/files")
        return data if isinstance(data, list) else []


# ── Claude API ─────────────────────────────────────────────────────────────────

class ClaudeClient:
    """Minimal Anthropic API client using stdlib only."""

    API = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model

    def review(self, prompt: str, system: str = REVIEW_SYSTEM_PROMPT) -> str:
        payload = json.dumps({
            "model": self.model,
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()

        req = urllib.request.Request(self.API, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("x-api-key", self.api_key)
        req.add_header("anthropic-version", ANTHROPIC_VERSION)
        req.add_header("User-Agent", USER_AGENT)

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data["content"][0]["text"]
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code == 401:
                raise SystemExit("Invalid ANTHROPIC_API_KEY.")
            if e.code == 429:
                raise SystemExit("Anthropic API rate limited. Wait a moment and retry.")
            raise SystemExit(f"Anthropic API error {e.code}: {body[:300]}")


# ── PR URL parsing ─────────────────────────────────────────────────────────────

def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL or shorthand into (owner, repo, number)."""
    # Full URL: https://github.com/owner/repo/pull/123
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))

    # Shorthand: owner/repo/123
    m = re.match(r"([^/]+)/([^/]+)/(\d+)$", url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))

    raise SystemExit(
        f"Cannot parse PR reference: {url}\n"
        "Expected: https://github.com/owner/repo/pull/123 or owner/repo/123"
    )


# ── Review logic ───────────────────────────────────────────────────────────────

def build_review_prompt(pr: PRInfo, diff: str, files: list[dict], focus: Optional[str]) -> str:
    """Build the prompt for Claude."""
    # Truncate diff if needed
    truncated = False
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS]
        truncated = True

    # Build file summary
    file_summary = ""
    if files:
        file_lines = []
        for f in files[:MAX_FILES_IN_DETAIL]:
            status = f.get("status", "?")
            additions = f.get("additions", 0)
            deletions = f.get("deletions", 0)
            name = f.get("filename", "?")
            file_lines.append(f"  {status:>10} +{additions}/-{deletions}  {name}")
        if len(files) > MAX_FILES_IN_DETAIL:
            file_lines.append(f"  ... and {len(files) - MAX_FILES_IN_DETAIL} more files")
        file_summary = "\n".join(file_lines)

    parts = [
        f"## PR Information",
        f"- Repository: {pr.owner}/{pr.repo}",
        f"- PR #{pr.number}: {pr.title}",
        f"- Author: {pr.author}",
        f"- Branch: {pr.head_branch} → {pr.base_branch}",
        f"- Files changed: {len(files)}",
    ]

    if pr.description:
        parts.append(f"\n## PR Description\n{pr.description}")

    if file_summary:
        parts.append(f"\n## Changed Files\n{file_summary}")

    if truncated:
        parts.append(f"\n⚠️ Diff truncated at {MAX_DIFF_CHARS:,} chars. Review the truncated portions with caution.")

    if focus:
        parts.append(f"\n## Review Focus\nPay special attention to: {focus}")

    parts.append(f"\n## Diff\n```diff\n{diff}\n```")

    return "\n".join(parts)


def review_pr(
    pr_url: str,
    github_token: Optional[str] = None,
    anthropic_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    focus: Optional[str] = None,
) -> ReviewResult:
    """Review a PR and return structured results."""
    owner, repo, number = parse_pr_url(pr_url)

    # Init clients
    gh = GitHubClient(token=github_token)

    if not anthropic_key:
        raise SystemExit(
            "ANTHROPIC_API_KEY not set.\n"
            "Export it: export ANTHROPIC_API_KEY=sk-ant-..."
        )
    claude = ClaudeClient(api_key=anthropic_key, model=model)

    # Fetch PR data
    print(f"Fetching PR #{number} from {owner}/{repo}...", file=sys.stderr)
    pr_info = gh.get_pr_info(owner, repo, number)
    diff = gh.get_pr_diff(owner, repo, number)
    files = gh.get_pr_files(owner, repo, number)

    print(f"Diff: {len(diff):,} chars, {len(files)} files", file=sys.stderr)

    # Build prompt and call Claude
    prompt = build_review_prompt(pr_info, diff, files, focus)
    print(f"Reviewing with {model}...", file=sys.stderr)
    review_md = claude.review(prompt)

    return ReviewResult(
        pr=pr_info,
        markdown=review_md,
        model=model,
        diff_chars=len(diff),
        files_changed=len(files),
        truncated=len(diff) > MAX_DIFF_CHARS,
    )


# ── Output formatting ──────────────────────────────────────────────────────────

def format_markdown(result: ReviewResult) -> str:
    """Format the review as a Markdown comment suitable for GitHub."""
    lines = [
        result.markdown,
        "",
        "---",
        f"<sub>Reviewed by [claude-review](https://github.com/claude-builders-bounty) "
        f"using `{result.model}` · "
        f"{result.files_changed} files, {result.diff_chars:,} chars diff"
        f"{' · diff truncated' if result.truncated else ''} · "
        f"{result.timestamp}</sub>",
    ]
    return "\n".join(lines)


def format_json(result: ReviewResult) -> str:
    """Format the review as JSON."""
    return json.dumps({
        "pr": {
            "owner": result.pr.owner,
            "repo": result.pr.repo,
            "number": result.pr.number,
            "title": result.pr.title,
            "url": result.pr.url,
        },
        "review": result.markdown,
        "model": result.model,
        "diff_chars": result.diff_chars,
        "files_changed": result.files_changed,
        "truncated": result.truncated,
        "timestamp": result.timestamp,
    }, indent=2, ensure_ascii=False)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="AI-powered PR review using Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              claude-review --pr https://github.com/vercel/next.js/pull/12345
              claude-review --pr vercel/next.js/12345 --focus security,performance
              claude-review --pr owner/repo/123 --format json > review.json

            Environment variables:
              ANTHROPIC_API_KEY  Required. Your Anthropic API key.
              GITHUB_TOKEN       Optional. For private repos / higher rate limits.
              CLAUDE_MODEL       Optional. Model name (default: claude-sonnet-4-5).
        """),
    )
    parser.add_argument(
        "--pr", required=True,
        help="PR URL (https://github.com/owner/repo/pull/123) or shorthand (owner/repo/123)",
    )
    parser.add_argument(
        "--focus", default=None,
        help="Comma-separated review focus areas (e.g., security,performance,testing)",
    )
    parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--model", default=None,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Write output to file instead of stdout",
    )

    args = parser.parse_args()

    # Resolve config
    github_token = os.environ.get("GITHUB_TOKEN")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    model = args.model or os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL)

    # Run review
    result = review_pr(
        pr_url=args.pr,
        github_token=github_token,
        anthropic_key=anthropic_key,
        model=model,
        focus=args.focus,
    )

    # Format output
    if args.format == "json":
        output = format_json(result)
    else:
        output = format_markdown(result)

    # Write
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
