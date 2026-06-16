#!/usr/bin/env python3
"""PR Reviewer — analyze a unified diff and emit a structured Markdown review.

Reads a git diff from --diff FILE, --pr <number|url> (via the `gh` CLI), or
stdin, sends it to the Claude API with the shared review prompt, and prints a
Markdown review comment (Summary / Risks / Suggestions / Confidence) to stdout.

Engine: Anthropic Messages API. Requires ANTHROPIC_API_KEY and `pip install
anthropic`. Designed to run identically on a laptop and in CI.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Default model. Override with --model or the PR_REVIEW_MODEL env var.
DEFAULT_MODEL = "claude-sonnet-4-6"
# Guardrail so an enormous diff cannot blow the context window or the bill.
MAX_DIFF_CHARS = 200_000

PROMPT_PATH = (
    Path(__file__).resolve().parent.parent / "prompts" / "review-system-prompt.md"
)


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        eprint(f"error: cannot read system prompt at {PROMPT_PATH}: {exc}")
        sys.exit(1)


def diff_from_pr(pr: str) -> tuple[str, str]:
    """Return (diff, context) for a PR number or URL using the gh CLI."""
    try:
        diff = subprocess.run(
            ["gh", "pr", "diff", pr],
            check=True, capture_output=True, text=True,
        ).stdout
        meta = subprocess.run(
            ["gh", "pr", "view", pr, "--json", "title,body"],
            check=True, capture_output=True, text=True,
        ).stdout
    except FileNotFoundError:
        eprint("error: `gh` CLI not found. Install GitHub CLI or use --diff/stdin.")
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        eprint(f"error: gh failed for PR '{pr}':\n{exc.stderr.strip()}")
        sys.exit(1)
    return diff, meta


def read_diff(args: argparse.Namespace) -> str:
    context = ""
    if args.pr:
        diff, context = diff_from_pr(args.pr)
    elif args.diff:
        try:
            diff = Path(args.diff).read_text(encoding="utf-8")
        except OSError as exc:
            eprint(f"error: cannot read diff file {args.diff}: {exc}")
            sys.exit(1)
    elif not sys.stdin.isatty():
        diff = sys.stdin.read()
    else:
        eprint("error: no diff provided. Use --pr, --diff FILE, or pipe via stdin.")
        sys.exit(2)

    if not diff.strip():
        eprint("error: the diff is empty — nothing to review.")
        sys.exit(2)

    if args.title:
        context = f'{{"title": {args.title!r}}}'

    truncated = False
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS]
        truncated = True

    user_msg = ""
    if context.strip():
        user_msg += f"PR metadata (JSON):\n{context.strip()}\n\n"
    if truncated:
        user_msg += (
            f"NOTE: the diff was truncated to the first {MAX_DIFF_CHARS} characters. "
            "Factor the missing context into your confidence score.\n\n"
        )
    user_msg += "Here is the unified diff to review:\n\n```diff\n" + diff + "\n```"
    return user_msg


def review(user_msg: str, system_prompt: str, model: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        eprint("error: ANTHROPIC_API_KEY is not set.")
        sys.exit(1)
    try:
        from anthropic import Anthropic
    except ImportError:
        eprint("error: the `anthropic` package is missing. Run: pip install anthropic")
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as exc:  # surface API/network errors cleanly for CI logs
        eprint(f"error: Claude API request failed: {exc}")
        sys.exit(1)

    return "".join(block.text for block in resp.content if block.type == "text").strip()


def main() -> None:
    p = argparse.ArgumentParser(
        prog="pr_review.py",
        description="Analyze a PR diff and print a structured Markdown review.",
    )
    src = p.add_mutually_exclusive_group()
    src.add_argument("--pr", help="PR number or URL (uses the `gh` CLI to fetch the diff)")
    src.add_argument("--diff", help="path to a .diff/.patch file")
    p.add_argument("--title", help="optional PR title to give the reviewer context")
    p.add_argument("--model", default=os.environ.get("PR_REVIEW_MODEL", DEFAULT_MODEL),
                   help=f"Claude model id (default: {DEFAULT_MODEL})")
    p.add_argument("--out", help="write the review to this file instead of stdout")
    args = p.parse_args()

    system_prompt = load_system_prompt()
    user_msg = read_diff(args)
    result = review(user_msg, system_prompt, args.model)

    if args.out:
        Path(args.out).write_text(result + "\n", encoding="utf-8")
        eprint(f"review written to {args.out}")
    else:
        print(result)


if __name__ == "__main__":
    main()
