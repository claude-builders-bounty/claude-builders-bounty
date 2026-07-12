#!/usr/bin/env python3
"""Claude Code PR review agent — structured Markdown review from a PR URL."""
from __future__ import annotations

import argparse
import os
import re
import sys

import requests

try:
    import anthropic
except ImportError:
    print("Install: pip install anthropic requests", file=sys.stderr)
    sys.exit(1)

PR_RE = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<num>\d+)",
    re.I,
)

SYSTEM = """You are an expert code reviewer. Given a pull request title, body, and diff,
produce a structured Markdown review with EXACTLY these sections:

## Summary
2–3 sentences describing what the PR changes.

## Identified Risks
- bullet list of concrete risks (security, regressions, perf, API breaks).
  If none, write: - None identified

## Improvement Suggestions
- bullet list of actionable improvements.
  If none, write: - None

## Confidence
One of: **Low** | **Medium** | **High**

Be concise and specific. Cite files/lines when possible."""


def parse_pr(url: str) -> tuple[str, str, int]:
    m = PR_RE.match(url.strip())
    if not m:
        raise SystemExit(f"Invalid PR URL: {url}")
    return m.group("owner"), m.group("repo"), int(m.group("num"))


def gh_headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "claude-review"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def fetch_pr(owner: str, repo: str, num: int) -> tuple[str, str, str]:
    base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}"
    r = requests.get(base, headers=gh_headers(), timeout=30)
    r.raise_for_status()
    meta = r.json()
    d = requests.get(
        base,
        headers={**gh_headers(), "Accept": "application/vnd.github.v3.diff"},
        timeout=60,
    )
    d.raise_for_status()
    diff = d.text
    # Cap huge diffs so the model stays focused
    if len(diff) > 80_000:
        diff = diff[:80_000] + "\n\n... [diff truncated] ...\n"
    return meta.get("title") or "", meta.get("body") or "", diff


def review(title: str, body: str, diff: str) -> str:
    client = anthropic.Anthropic()
    user = (
        f"# PR Title\n{title}\n\n# PR Body\n{body or '(empty)'}\n\n"
        f"# Diff\n```diff\n{diff}\n```"
    )
    msg = client.messages.create(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=2048,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()


def main() -> None:
    p = argparse.ArgumentParser(description="Claude PR review agent")
    p.add_argument("--pr", required=True, help="GitHub PR URL")
    args = p.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY")
    owner, repo, num = parse_pr(args.pr)
    title, body, diff = fetch_pr(owner, repo, num)
    print(review(title, body, diff))


if __name__ == "__main__":
    main()
