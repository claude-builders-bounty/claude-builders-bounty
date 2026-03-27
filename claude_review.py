#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

PROMPT_TEMPLATE = '''You are reviewing a GitHub pull request diff.
Return ONLY structured Markdown with these sections exactly:

## Summary
2-3 sentence summary.

## Risks
- bullet list

## Suggestions
- bullet list

## Confidence
One of: Low / Medium / High

PR URL: {pr_url}

Diff:
{diff}
'''


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def fetch_diff(pr_url: str) -> str:
    return run(["gh", "pr", "diff", pr_url])


def parse_pr_url(pr_url: str):
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        raise ValueError("Invalid GitHub PR URL")
    owner, repo, number = m.groups()
    return owner, repo, number


def call_claude(prompt: str) -> str:
    if shutil_which("claude"):
        return run(["claude", "--permission-mode", "bypassPermissions", "--print", prompt]).strip()
    if shutil_which("agent"):
        return run(["agent", "--trust", "-p", prompt, "--output-format", "text"]).strip()
    raise RuntimeError("Neither claude nor agent CLI is available")


def shutil_which(name: str):
    from shutil import which
    return which(name)


def ensure_structure(text: str) -> str:
    required = ["## Summary", "## Risks", "## Suggestions", "## Confidence"]
    missing = [h for h in required if h not in text]
    if missing:
        raise ValueError(f"Model output missing sections: {', '.join(missing)}")
    return text.strip() + "\n"


def post_comment(pr_url: str, body: str):
    run(["gh", "pr", "comment", pr_url, "--body", body])


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR diff with Claude")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--max-diff-chars", type=int, default=20000)
    parser.add_argument("--out", help="Write output to file")
    parser.add_argument("--post-comment", action="store_true")
    args = parser.parse_args()

    diff = fetch_diff(args.pr)
    diff = diff[: args.max_diff_chars]
    prompt = PROMPT_TEMPLATE.format(pr_url=args.pr, diff=diff)
    review = ensure_structure(call_claude(prompt))

    if args.out:
        Path(args.out).write_text(review, encoding="utf-8")
    else:
        sys.stdout.write(review)

    if args.post_comment:
        post_comment(args.pr, review)


if __name__ == "__main__":
    main()
