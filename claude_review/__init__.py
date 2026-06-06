#!/usr/bin/env python3
"""claude-review — Claude Code sub-agent that reviews a GitHub Pull Request
and emits a structured Markdown review comment.

Usage:
    ANTHROPIC_API_KEY=sk-... python -m claude_review --pr https://github.com/owner/repo/pull/123
    ANTHROPIC_API_KEY=sk-... python -m claude_review --diff /path/to/local.diff

Output: a Markdown string with sections: Summary, Risks, Suggestions, Confidence.

The agent uses the Claude API to analyse the PR diff and follows a strict
JSON schema so the Markdown can be regenerated deterministically.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class Review:
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str  # Low | Medium | High

    def to_markdown(self) -> str:
        risks_md = "\n".join(f"- {r}" for r in self.risks) or "- None identified"
        sugg_md = "\n".join(f"- {s}" for s in self.suggestions) or "- None identified"
        return (
            f"## 🤖 Claude Code Review\n\n"
            f"### Summary\n{self.summary}\n\n"
            f"### ⚠️ Risks\n{risks_md}\n\n"
            f"### 💡 Suggestions\n{sugg_md}\n\n"
            f"**Confidence:** `{self.confidence}`\n"
        )


# ---- GitHub helpers ----------------------------------------------------------

_GH_TOKEN = os.environ.get("GITHUB_TOKEN", os.environ.get("GH_TOKEN", ""))


def gh_request(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url)
    if _GH_TOKEN:
        req.add_header("Authorization", f"Bearer {_GH_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"github error {e.code}: {e.read().decode()[:200]}")


_PR_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = _PR_RE.match(url.strip())
    if not m:
        raise SystemExit(f"not a PR url: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_pr_diff(pr_url: str) -> tuple[dict[str, Any], str]:
    owner, repo, num = parse_pr_url(pr_url)
    meta = gh_request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}")
    diff_req = urllib.request.Request(meta["diff_url"])
    if _GH_TOKEN:
        diff_req.add_header("Authorization", f"Bearer {_GH_TOKEN}")
    diff_req.add_header("Accept", "application/vnd.github.v3.diff")
    with urllib.request.urlopen(diff_req, timeout=30) as r:
        diff = r.read().decode("utf-8", errors="replace")
    return meta, diff


def truncate_diff(diff: str, max_chars: int = 60_000) -> str:
    """Cap the diff at max_chars to keep the prompt well within context window."""
    if len(diff) <= max_chars:
        return diff
    return diff[:max_chars] + "\n\n... (truncated; PR has {} more characters)".format(
        len(diff) - max_chars
    )


# ---- Claude API --------------------------------------------------------------


def _anthropic_post(path: str, body: dict[str, Any]) -> dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY env var is required")
    req = urllib.request.Request(f"https://api.anthropic.com{path}", data=json.dumps(body).encode())
    req.add_header("x-api-key", api_key)
    req.add_header("anthropic-version", "2023-06-01")
    req.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"anthropic error {e.code}: {e.read().decode()[:300]}")


SYSTEM_PROMPT = """You are Claude, an expert code reviewer for pull requests.
Given the unified diff of a PR, produce a concise, structured review as JSON.

Strict output schema (no extra keys, no markdown fences, no commentary):
{{
  "summary": "<2-3 sentence overview of what the PR does>",
  "risks": ["<short bullet>", ...],
  "suggestions": ["<short bullet>", ...],
  "confidence": "Low" | "Medium" | "High"
}}

Rules:
- Be specific. Reference file names, function names, line intent.
- Never invent changes. If the diff is empty or trivial, say so.
- Risks and suggestions must be actionable, not generic platitudes.
- Confidence reflects how certain you are about the correctness of the change;
  High = straightforward refactor/docs, Medium = feature with tests, Low = subtle
  logic/security change or large blast radius.
"""


def review_with_claude(diff: str, pr_meta: dict[str, Any]) -> Review:
    user_prompt = (
        f"PR title: {pr_meta.get('title', '')}\n"
        f"PR author: {pr_meta.get('user', {}).get('login', '')}\n"
        f"PR description:\n{(pr_meta.get('body') or '')[:2000]}\n\n"
        f"Diff:\n```diff\n{truncate_diff(diff)}\n```"
    )
    raw = _anthropic_post(
        "/v1/messages",
        {
            "model": "claude-opus-4-7",
            "max_tokens": 2048,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        },
    )
    text = "".join(b.get("text", "") for b in raw.get("content", []) if b.get("type") == "text")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise SystemExit(f"claude returned non-JSON:\n{text[:500]}")
        data = json.loads(m.group(0))
    return Review(
        summary=data.get("summary", "").strip(),
        risks=[r.strip() for r in data.get("risks", []) if r.strip()],
        suggestions=[s.strip() for s in data.get("suggestions", []) if s.strip()],
        confidence=data.get("confidence", "Medium").strip(),
    )


# ---- CLI ---------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="claude-review", description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--pr", help="GitHub PR URL, e.g. https://github.com/o/r/pull/123")
    g.add_argument("--diff", help="Path to a local unified diff file")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    args = p.parse_args(argv)

    if args.pr:
        meta, diff = fetch_pr_diff(args.pr)
    else:
        with open(args.diff, "r", encoding="utf-8") as f:
            diff = f.read()
        meta = {"title": "(local diff)", "user": {"login": "local"}, "body": ""}

    review = review_with_claude(diff, meta)
    if args.json:
        print(json.dumps(review.__dict__, indent=2))
    else:
        print(review.to_markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
