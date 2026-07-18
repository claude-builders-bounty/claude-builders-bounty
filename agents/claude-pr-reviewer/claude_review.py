#!/usr/bin/env python3
"""
claude_review.py — Standalone Claude-powered PR review CLI.

Usage:
    python3 agents/claude-pr-reviewer/claude_review.py \
        --pr https://github.com/owner/repo/pull/123 \
        --anthropic-key "$ANTHROPIC_API_KEY" \
        --out review.md

If no Anthropic key is provided and the `claude` CLI is on PATH, the script
will shell out to `claude -p` so it works inside Claude Code without
requiring a separate API key.

Output: a single Markdown file with the structured review.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _http_get_json(url: str, token: str | None = None) -> Any:
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "claude-review-cli/1.0")
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    m = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?", pr_url.strip())
    if not m:
        raise ValueError(f"Not a GitHub PR URL: {pr_url!r}")
    return m.group(1), m.group(2), int(m.group(3))


def _fetch_diff(owner: str, repo: str, number: int, token: str | None) -> str:
    base = f"https://patch-diff.githubusercontent.com/raw/{owner}/{repo}/pull/{number}.diff"
    req = urllib.request.Request(base)
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "claude-review-cli/1.0")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        # Fallback: GitHub's API diff endpoint
        if exc.code == 406:
            api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
            meta = _http_get_json(api, token)
            return meta.get("body") or "(empty PR body)"
        raise


def _build_prompt(diff: str, pr_meta: dict[str, Any]) -> str:
    return (
        "You are reviewing the following GitHub pull request. "
        "Produce a structured review with FOUR sections, in this exact order:\n"
        "  ## Summary\n  (2-3 sentences, scope + intent)\n"
        "  ## Risks\n  (bulleted list, each a real defect or maintainability concern, not \"look closer\")\n"
        "  ## Suggestions\n  (bulleted list, each an actionable change)\n"
        "  ## Confidence\n  (one of: Low / Medium / High)\n\n"
        f"PR title: {pr_meta.get('title','')}\n"
        f"PR body (truncated to 500 chars):\n{(pr_meta.get('body') or '')[:500]}\n\n"
        f"Diff (truncated to 60_000 chars):\n{diff[:60_000]}\n\n"
        "Reply only with Markdown, no preamble."
    )


def _call_claude(prompt: str, model: str, api_key: str | None) -> str:
    if api_key:
        # Use Anthropic's Messages API
        req = urllib.request.Request("https://api.anthropic.com/v1/messages")
        req.add_header("x-api-key", api_key)
        req.add_header("anthropic-version", "2023-06-01")
        req.add_header("content-type", "application/json")
        body = json.dumps({
            "model": model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        with urllib.request.urlopen(req, data=body, timeout=120) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"]

    # Fallback to `claude -p` CLI (already authenticated in the user's session)
    try:
        out = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, check=True, timeout=180,
        )
        return out.stdout.strip()
    except FileNotFoundError:
        sys.stderr.write(
            "error: neither ANTHROPIC_API_KEY env var nor `claude` CLI was found.\n"
            "Set ANTHROPIC_API_KEY or install Claude Code and run `claude login`.\n"
        )
        sys.exit(2)


def _render_markdown(review: str, pr_url: str, owner: str, repo: str, number: int) -> str:
    return (
        f"# PR Review: {owner}/{repo}#{number}\n\n"
        f"Source: <{pr_url}>\n\n"
        "---\n\n"
        f"{review.strip()}\n"
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pr", required=True, help="GitHub PR URL")
    p.add_argument("--anthropic-key", default=os.environ.get("ANTHROPIC_API_KEY"),
                   help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    p.add_argument("--github-token", default=os.environ.get("GITHUB_TOKEN"),
                   help="GitHub token for private PRs (or set GITHUB_TOKEN env var)")
    p.add_argument("--model", default="claude-opus-4-7",
                   help="Anthropic model (default claude-opus-4-7)")
    p.add_argument("--out", default="review.md", help="Output file (default review.md)")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        owner, repo, number = _parse_pr_url(args.pr)
    except (ValueError, SystemExit) as exc:
        sys.stderr.write(f"arg error: {exc}\n")
        return 2

    sys.stderr.write(f"Fetching {owner}/{repo}#{number} diff...\n")
    diff = _fetch_diff(owner, repo, number, args.github_token)

    meta: dict[str, Any] = {}
    try:
        meta = _http_get_json(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
            args.github_token,
        )
    except Exception:  # noqa: BLE001
        meta = {"title": "", "body": ""}

    sys.stderr.write(f"Reviewing with {args.model}...\n")
    review_text = _call_claude(_build_prompt(diff, meta), args.model, args.anthropic_key)

    md = _render_markdown(review_text, args.pr, owner, repo, number)
    Path(args.out).write_text(md, encoding="utf-8")
    sys.stderr.write(f"Wrote {args.out} ({len(md)} bytes)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
