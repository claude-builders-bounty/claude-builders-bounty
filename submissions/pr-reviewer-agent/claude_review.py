#!/usr/bin/env python3
"""claude-review — Structured Markdown PR review via Claude.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --model claude-sonnet-4-5
    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

Requires:
    - gh CLI (authenticated)
    - ANTHROPIC_API_KEY env var (or OAuth token via `claude setup-token`)
    - anthropic Python SDK: pip install anthropic

Output: structured Markdown with Summary / Risks / Suggestions / Confidence
(printed to stdout; also written to --output if specified).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: install with `pip install anthropic`", file=sys.stderr)
    sys.exit(2)


PR_URL_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")

MODEL_DEFAULT = "claude-sonnet-4-5"


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = PR_URL_RE.match(url.strip())
    if not m:
        raise ValueError(f"not a github PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def gh(*args: str) -> str:
    r = subprocess.run(
        ["gh", *args], capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=60,
    )
    if r.returncode != 0:
        raise RuntimeError(f"gh failed ({' '.join(args)}): {r.stderr.strip()[:300]}")
    return r.stdout


def fetch_pr_metadata(owner: str, repo: str, num: int) -> dict:
    raw = gh("pr", "view", f"{num}", "--repo", f"{owner}/{repo}",
            "--json", "title,body,author,additions,deletions,changedFiles,baseRefName,headRefName,state,url")
    return json.loads(raw)


def fetch_pr_diff(owner: str, repo: str, num: int) -> str:
    return gh("pr", "diff", f"{num}", "--repo", f"{owner}/{repo}")


REVIEW_PROMPT = """You are a senior code reviewer. Below is a GitHub pull request. Produce a structured Markdown review.

Pull Request: {url}
Title: {title}
Author: {author}
Base: {base} ← Head: {head}
Changed files: {changed_files} ({additions} additions, {deletions} deletions)

Description:
{body}

Diff:
```
{diff}
```

Produce ONLY the following Markdown (no preamble, no code fence, no closing remarks):

## Summary
<2-3 sentences explaining what the PR changes and why.>

## Risks
<Bulleted list of 2-6 concrete risks. Each bullet must reference a specific file or behavior. If no real risks, write a single bullet: "- No material risks identified.">

## Suggestions
<Bulleted list of 2-6 concrete actionable suggestions. Each must be specific (file + line range or behavior). If nothing to suggest, write: "- Looks ready to merge as-is.">

## Confidence: <Low|Medium|High>
<1 sentence justifying the confidence level. Low = high uncertainty / large surface / unfamiliar domain. Medium = standard PR with clear scope. High = small, well-tested, low-risk change.>

Hard rules:
- Reference specific files / functions / lines from the diff, not vague generalities.
- DO NOT speculate about intent — base findings on what the diff shows.
- Flag breaking changes, missing tests, security implications, performance regressions if visible.
- Style / nit issues belong in Suggestions, not Risks.
- Be honest about confidence — small typo fixes are High, sweeping refactors are Low."""


def build_client() -> Anthropic:
    """Auto-detect API key vs OAuth token.

    - `sk-ant-api*` → standard API key (X-Api-Key)
    - `sk-ant-oat*` → OAuth token from Claude Code/Pro (Authorization: Bearer)
      Uses the SDK's native `auth_token` parameter.
    """
    token = os.environ.get("ANTHROPIC_API_KEY", "")
    if token.startswith("sk-ant-oat"):
        return Anthropic(auth_token=token)
    return Anthropic(api_key=token or None)


def review(url: str, model: str = MODEL_DEFAULT, max_diff_chars: int = 60000) -> str:
    owner, repo, num = parse_pr_url(url)
    print(f"[claude-review] fetching {owner}/{repo}#{num} ...", file=sys.stderr)
    meta = fetch_pr_metadata(owner, repo, num)
    diff = fetch_pr_diff(owner, repo, num)
    if len(diff) > max_diff_chars:
        diff = diff[:max_diff_chars] + f"\n\n[...truncated, original diff was {len(diff)} chars]"

    prompt = REVIEW_PROMPT.format(
        url=url,
        title=meta.get("title", ""),
        author=meta.get("author", {}).get("login", "?"),
        base=meta.get("baseRefName", "?"),
        head=meta.get("headRefName", "?"),
        changed_files=meta.get("changedFiles", "?"),
        additions=meta.get("additions", "?"),
        deletions=meta.get("deletions", "?"),
        body=(meta.get("body") or "(no description)")[:2000],
        diff=diff,
    )

    client = build_client()
    print(f"[claude-review] requesting review from {model} ...", file=sys.stderr)
    resp = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


def main() -> int:
    p = argparse.ArgumentParser(prog="claude-review",
        description="Structured Markdown PR review via Claude.")
    p.add_argument("--pr", required=True, help="GitHub PR URL")
    p.add_argument("--model", default=MODEL_DEFAULT,
                   help=f"Anthropic model (default: {MODEL_DEFAULT})")
    p.add_argument("--output", help="write Markdown to this file in addition to stdout")
    p.add_argument("--max-diff-chars", type=int, default=60000,
                   help="truncate diff before sending to model (default 60K chars)")
    args = p.parse_args()

    try:
        md = review(args.pr, model=args.model, max_diff_chars=args.max_diff_chars)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    print(md)
    if args.output:
        Path(args.output).write_text(md + "\n", encoding="utf-8")
        print(f"\n[claude-review] also wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
