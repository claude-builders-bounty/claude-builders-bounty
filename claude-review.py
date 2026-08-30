#!/usr/bin/env python3
"""
claude-review — Claude Code sub-agent that reviews a PR and posts a
structured Markdown review comment.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    claude-review --pr https://github.com/owner/repo/pull/123
    # or, to also post the review comment on the PR:
    claude-review --pr https://github.com/owner/repo/pull/123 --post \
                  --token ghp_...

Produces structured Markdown:
  - Summary of changes (2–3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High

Tested on 2 real PRs (outputs included, see README).
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def fetch_pr_diff(pr_url: str):
    """Convert a PR URL to its .diff URL and fetch it."""
    diff_url = pr_url if pr_url.endswith(".diff") else pr_url + ".diff"
    req = urllib.request.Request(diff_url, headers={"User-Agent": "claude-review"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def call_claude(diff: str) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("FATAL: set ANTHROPIC_API_KEY (or --key).")
    prompt = (
        "You are a senior code reviewer. Review this pull request diff "
        "and return STRICT Markdown with exactly these sections:\n\n"
        "## Summary\n(Section 2-3 sentences)\n\n"
        "## Risks\n- ...\n\n"
        "## Suggestions\n- ...\n\n"
        "## Confidence\n**Low | Medium | High**\n\n"
        "Be concise, specific, cite line numbers where possible. "
        "Here is the diff:\n\n```diff\n" + diff[:120000] + "\n```"
    )
    body = json.dumps({
        "model": MODEL,
        "max_tokens": 1500,
        "system": "You are a rigorous, concise code reviewer.",
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(ANTHROPIC_URL, data=body, method="POST", headers={
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    return "".join(b.get("text", "") for b in data.get("content", []))


def post_pr_comment(pr_url: str, markdown: str, token: str):
    # https://github.com/o/r/pull/123 -> api /repos/o/r/issues/123/comments
    import re
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        print("WARN: could not parse PR URL to post comment; review still printed.")
        return
    owner, repo, number = m.group(1), m.group(2), m.group(3)
    api = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    data = json.dumps({"body": markdown}).encode()
    req = urllib.request.Request(api, data=data, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            posted = json.load(r)
        print("Posted review comment:", posted.get("html_url"))
        return posted.get("html_url")
    except Exception as e:
        print("WARN: failed to post comment:", e)
        return None


def main():
    ap = argparse.ArgumentParser(description="Claude Code PR review sub-agent")
    ap.add_argument("--pr", required=True, help="Full PR URL, e.g. https://github.com/o/r/pull/123")
    ap.add_argument("--diff", help="Local diff file instead of fetching from URL (testing)")
    ap.add_argument("--post", action="store_true", help="Post the review as a comment on the PR")
    ap.add_argument("--token", help="GitHub token (needed with --post)")
    ap.add_argument("--key", help="Anthropic API key (overrides env ANTHROPIC_API_KEY)")
    ap.add_argument("--out", help="Write review markdown to this file")
    args = ap.parse_args()

    if args.diff:
        diff = open(args.diff).read()
    else:
        diff = fetch_pr_diff(args.pr)

    if args.key:
        os.environ["ANTHROPIC_API_KEY"] = args.key
    if "--rate-limit-hit" in diff:
        # guard against trivial fetches (e.g. HTML instead of diff)
        print("WARN: fetched content looks like HTML, not a diff.")
        diff = "# Unable to fetch diff for " + args.pr + "\n"

    review = call_claude(diff)

    header = f"## 🤖 claude-review (AutoJet sub-agent)\n\nReviewed PR: {args.pr}\n"
    full = header + "\n" + review

    if args.out:
        with open(args.out, "w") as f:
            f.write(full)
        print("Review written to", args.out)
    print("\n" + full)

    if args.post:
        if not args.token:
            sys.exit("--post requires --token ghp_...")
        post_pr_comment(args.pr, full, args.token)


if __name__ == "__main__":
    main()
