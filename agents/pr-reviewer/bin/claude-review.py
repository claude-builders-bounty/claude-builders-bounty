#!/usr/bin/env python3
"""
claude-review — fetch a GitHub PR diff, hand it to Claude (via the local Claude
Code CLI or the Anthropic API), and emit a structured Markdown review comment
with Summary / Risks / Improvement suggestions / Confidence.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  cat my.diff | claude-review --stdin
  claude-review --diff-file path/to.diff
  claude-review --pr <url> --post   # also post the comment back to the PR

Auth, in priority order:
  - ANTHROPIC_API_KEY (direct API)
  - claude CLI on PATH (uses the user's OAuth login)

GitHub auth via GITHUB_TOKEN / GH_TOKEN; falls back to `gh` CLI if installed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Force UTF-8 on stdout so em-dashes / unicode in the review aren't mangled when
# the output is redirected to a file on Windows (default cp1252).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROMPT_TEMPLATE = """You are a senior code reviewer. Read the pull-request below and produce a single structured Markdown review comment.

Output EXACTLY this shape — no preamble, no closing thoughts:

## Summary
<2-3 sentences. What this PR is about and the overall change shape.>

## Risks
<one bullet per risk. If none: "- _none identified_".>

## Improvement suggestions
<one bullet per suggestion. If none: "- _none_".>

**Confidence:** <Low|Medium|High>

Confidence rules:
- High: small (<200 LOC), self-contained, mechanical changes (rename / dep bump / format) where the diff is its own justification.
- Medium: a real change with adequate test coverage in the diff.
- Low: large (>1000 LOC), missing context (private deps, no tests in diff), or multiple unrelated changes bundled.

PR title: {title}
PR url:   {url}
Author:   {author}
Lines added/removed: +{additions} / -{deletions}

--- DIFF (truncated if very large) ---
{diff}
--- END DIFF ---
"""

DIFF_LIMIT = 60_000  # characters; ~1000-1500 lines typical


def _gh_api(path: str, token: str | None) -> dict:
    headers = {"User-Agent": "claude-review/1.0", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _gh_diff(owner: str, repo: str, num: int, token: str | None) -> str:
    headers = {"User-Agent": "claude-review/1.0", "Accept": "application/vnd.github.v3.diff"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}", headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def _parse_pr_url(url: str) -> tuple[str, str, int]:
    m = re.match(r"https?://github\.com/([\w.-]+)/([\w.-]+)/pull/(\d+)", url.strip())
    if not m:
        raise ValueError(f"not a github pull URL: {url!r}")
    return m.group(1), m.group(2), int(m.group(3))


def _truncate_diff(diff: str) -> str:
    if len(diff) <= DIFF_LIMIT:
        return diff
    head = diff[: DIFF_LIMIT - 200]
    return head + "\n...\n[diff truncated to ~60k chars; agent should escalate confidence to Low]\n"


def _call_via_claude_cli(prompt: str, model: str | None) -> str:
    binary = shutil.which("claude") or shutil.which("claude.exe")
    if not binary:
        raise RuntimeError("`claude` not on PATH")
    # Pipe the prompt via stdin to avoid Windows argv length limits (~32k).
    cmd = [binary, "--print", "--output-format", "json", "--no-session-persistence"]
    if model:
        cmd += ["--model", model]
    cp = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )
    if cp.returncode != 0:
        raise RuntimeError(f"claude CLI failed (rc={cp.returncode}): {cp.stderr.strip()[:600]}")
    try:
        payload = json.loads(cp.stdout)
        return payload.get("result") or cp.stdout
    except json.JSONDecodeError:
        return cp.stdout


def _call_via_api(prompt: str, api_key: str, model: str = "claude-sonnet-4-5") -> str:
    body = json.dumps({
        "model": model,
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body, method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
            return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Anthropic API error {e.code}: {e.read().decode()[:500]}")


def review(prompt: str, model: str | None) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        return _call_via_api(prompt, api_key, model or "claude-sonnet-4-5")
    return _call_via_claude_cli(prompt, model)


def _post_pr_comment(owner: str, repo: str, num: int, token: str, body: str) -> str:
    payload = json.dumps({"body": body}).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{num}/comments",
        data=payload, method="POST",
        headers={
            "User-Agent": "claude-review/1.0",
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()).get("html_url", "")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--pr", help="GitHub PR URL")
    src.add_argument("--stdin", action="store_true", help="Read unified diff from stdin")
    src.add_argument("--diff-file", help="Read unified diff from file")
    p.add_argument("--model", default=None, help="Override Claude model (default: sonnet)")
    p.add_argument("--post", action="store_true", help="Post the review back as a PR comment (requires --pr + GITHUB_TOKEN)")
    args = p.parse_args()

    gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    if args.pr:
        owner, repo, num = _parse_pr_url(args.pr)
        meta = _gh_api(f"/repos/{owner}/{repo}/pulls/{num}", gh_token)
        diff = _gh_diff(owner, repo, num, gh_token)
        prompt = PROMPT_TEMPLATE.format(
            title=meta.get("title", ""),
            url=args.pr,
            author=(meta.get("user") or {}).get("login", ""),
            additions=meta.get("additions", "?"),
            deletions=meta.get("deletions", "?"),
            diff=_truncate_diff(diff),
        )
    else:
        if args.diff_file:
            diff = Path(args.diff_file).read_text(encoding="utf-8", errors="replace")
        else:
            diff = sys.stdin.read()
        prompt = PROMPT_TEMPLATE.format(
            title="(pipe-input)", url="(pipe-input)", author="(pipe-input)",
            additions="?", deletions="?", diff=_truncate_diff(diff),
        )

    review_md = review(prompt, args.model).strip()
    sys.stdout.write(review_md + "\n")

    if args.post:
        if not args.pr:
            print("--post requires --pr", file=sys.stderr)
            return 2
        if not gh_token:
            print("--post requires GITHUB_TOKEN / GH_TOKEN", file=sys.stderr)
            return 2
        url = _post_pr_comment(owner, repo, num, gh_token, review_md)
        print(f"\nPosted: {url}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
