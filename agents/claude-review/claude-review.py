#!/usr/bin/env python3
"""claude-review — PR review agent producing structured Markdown.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --diff path/to/diff.patch

Requires ANTHROPIC_API_KEY in the environment.
"""
import argparse
import os
import subprocess
import sys
import urllib.request
import json

ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"


def fetch_diff(pr_url: str) -> str:
    # Use gh CLI to get the PR diff.
    out = subprocess.check_output(
        ["gh", "pr", "diff", pr_url], text=True, stderr=subprocess.STDOUT
    )
    return out


def read_diff(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def review(diff: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")

    prompt = (
        "You are a senior code reviewer. Review the following PR diff and return a "
        "structured Markdown review with these sections:\n"
        "## Summary\n(2-3 sentences)\n"
        "## Identified risks\n- bullet list\n"
        "## Improvement suggestions\n- bullet list\n"
        "## Confidence score\nLow / Medium / High\n\n"
        "Diff:\n```\n" + diff[:40000] + "\n```"
    )

    body = {
        "model": MODEL,
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        ANTHROPIC_API,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["content"][0]["text"]


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pr", help="PR URL")
    g.add_argument("--diff", help="Path to a diff/patch file")
    args = ap.parse_args()

    if args.pr:
        diff = fetch_diff(args.pr)
    else:
        diff = read_diff(args.diff)

    print(review(diff))
    return 0


if __name__ == "__main__":
    sys.exit(main())