#!/usr/bin/env python3
"""
claude-review — AI code-review agent for GitHub pull requests.

Fetches a PR's diff (+title/body context) via the GitHub CLI (`gh`) and returns
a structured Markdown review: Summary, Risks, Suggestions, Confidence score.

LLM backend: Anthropic Messages API over HTTPS using ONLY the Python standard
library (urllib) — zero pip installs. Reads ANTHROPIC_API_KEY from the env.

Usage:
  python claude_review.py --pr https://github.com/owner/repo/pull/123
  python claude_review.py --repo owner/repo --number 123 [--write out.md]
  python claude_review.py --diff-file local.patch   # review a local diff

Exit codes: 0 success · 1 usage/API error · 2 environment error (gh/key missing).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_DIFF_CHARS = int(os.environ.get("CLAUDE_REVIEW_MAX_DIFF", "120000"))
MAX_META_CHARS = 2000
GH = r"C:\tools\gh.exe" if os.name == "nt" and os.path.exists(r"C:\tools\gh.exe") else "gh"

PR_URL_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")

SYSTEM_PROMPT = """You are a senior code reviewer. You receive the title, description,
and unified diff of a GitHub pull request. Respond ONLY with Markdown matching exactly:

## Summary
(2-3 sentences describing what changed and why)

## Risks
- (each risk on one line; write "- None identified." if there are none)

## Suggestions
- (concrete improvement suggestions; write "- None." if none)

## Confidence
High | Medium | Low  followed by an em dash and one short justification sentence.

Rules: be specific (reference real file names, functions, and hunks from the diff);
judge risk from the maintainer's perspective (regressions, edge cases, tests missing);
do not restate the diff line-by-line; no preamble; no closing remarks."""


class ReviewError(Exception):
    """Expected failure with a clean user-facing message."""


def parse_pr(args):
    """Return (full_repo, number_str) from CLI args."""
    if args.pr:
        m = PR_URL_RE.search(args.pr)
        if not m:
            raise ReviewError(f"could not parse PR url: {args.pr!r}")
        return f"{m.group(1)}/{m.group(2)}", m.group(3)
    if args.repo and args.number:
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo):
            raise ReviewError(f"--repo must look like owner/name, got {args.repo!r}")
        return args.repo, str(args.number)
    raise ReviewError("provide --pr URL, or both --repo owner/name and --number N")


def _run_gh(gh_args, timeout=120):
    try:
        proc = subprocess.run([GH] + gh_args, capture_output=True,
                              text=True, errors="replace", timeout=timeout)
    except FileNotFoundError:
        raise ReviewError(
            "gh CLI not found on PATH. Install https://cli.github.com/ and run `gh auth login`."
        )
    except subprocess.TimeoutExpired:
        raise ReviewError(f"timed out running: gh {' '.join(gh_args[:3])} ...")
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise ReviewError(f"`gh {' '.join(gh_args[:4])}` failed: {detail[:300]}")
    return proc.stdout


def fetch_pr_context(repo, number):
    """Return (meta_text, diff_text). meta includes title/body for better reviews."""
    meta_raw = _run_gh(["pr", "view", str(number), "--repo", repo,
                        "--json", "title,body,author,baseRefName,headRefName"])
    try:
        meta = json.loads(meta_raw)
    except json.JSONDecodeError:
        meta = {}
    lines = [f"PR #{number} in {repo}"]
    if meta.get("author"):
        lines.append(f"Author: {meta['author'].get('login', 'unknown')}")
    if meta.get("title"):
        lines.append(f"Title: {meta['title']}")
    if meta.get("baseRefName") and meta.get("headRefName"):
        lines.append(f"Branches: {meta['baseRefName']} <- {meta['headRefName']}")
    body = (meta.get("body") or "").strip()
    if body:
        lines.append("Description:\n" + body[:MAX_META_CHARS])
    diff = _run_gh(["pr", "diff", str(number), "--repo", repo])
    if not diff.strip():
        raise ReviewError("the PR has an empty diff — nothing to review")
    return "\n".join(lines), diff


def truncate_middle(text, limit=MAX_DIFF_CHARS):
    """Keep head (half) + tail (quarter) with an explicit notice between."""
    if len(text) <= limit:
        return text
    head, tail = text[: limit // 2], text[-limit // 4:]
    notice = (f"\n\n[... truncated by claude-review: showing {len(head) + len(tail)} "
              f"of {len(text)} characters ...]\n")
    return head + notice + tail


def call_llm(context, diff):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ReviewError(
            "ANTHROPIC_API_KEY is not set.\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...   # see README setup"
        )
    payload = {
        "model": os.environ.get("CLAUDE_REVIEW_MODEL", DEFAULT_MODEL),
        "max_tokens": 1500,
        "system": SYSTEM_PROMPT,
        "messages": [{
            "role": "user",
            "content": (
                f"{context}\n\nDiff:\n```diff\n{truncate_middle(diff)}\n```\n\n"
                "Produce the structured review now."
            ),
        }],
    }
    req = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode(), method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        snippet = exc.read().decode(errors="replace")[:300]
        hint = (" (check your API key/billing)" if exc.code in (401, 403)
                else " (rate limited — retry shortly)" if exc.code == 429 else "")
        raise ReviewError(f"Anthropic API error {exc.code}{hint}: {snippet}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ReviewError(f"network request failed: {exc}")
    try:
        return "".join(block.get("text", "") for block in data["content"])
    except (KeyError, TypeError) as exc:
        raise ReviewError(f"unexpected API response shape: {exc}")


def build_review(args):
    """Do everything except printing; returns (header, review_md)."""
    if args.diff_file:
        with open(args.diff_file, encoding="utf-8", errors="replace") as fh:
            diff = fh.read()
        if not diff.strip():
            raise ReviewError(f"diff file is empty: {args.diff_file}")
        context = f"Local diff file: {args.diff_file}"
        header = "<!-- claude-review -->\n\n"
    else:
        repo, number = parse_pr(args)
        context, diff = fetch_pr_context(repo, number)
        header = f"<!-- claude-review of {repo}#{number} -->\n\n"
    return header, call_llm(context, diff)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="claude-review",
        description="AI code-review agent: PR URL in, structured Markdown review out.",
    )
    ap.add_argument("--pr", metavar="URL",
                    help="full PR URL, e.g. https://github.com/o/r/pull/123")
    ap.add_argument("--repo", metavar="OWNER/NAME", help="repository (with --number)")
    ap.add_argument("--number", metavar="N", help="PR number (with --repo)")
    ap.add_argument("--write", metavar="FILE", help="also write the review to FILE")
    ap.add_argument("--diff-file", metavar="PATH",
                    help="review a local diff/patch file instead of fetching via gh")
    args = ap.parse_args(argv)

    try:
        header, review = build_review(args)
    except ReviewError as exc:
        print(f"claude-review: error: {exc}", file=sys.stderr)
        return 1

    output = header + review.rstrip() + "\n"
    sys.stdout.write(output)
    if args.write:
        with open(args.write, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"(written to {args.write})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
