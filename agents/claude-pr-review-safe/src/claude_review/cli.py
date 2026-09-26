"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

from .github import (
    GitHubError,
    PullRequest,
    fetch_pull_request_diff,
    parse_pull_request_url,
)
from .review import ReviewError, render_markdown, run_claude_review


def _positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(parsed) or parsed <= 0 or parsed > 900:
        raise argparse.ArgumentTypeError("must be between 0 and 900 seconds")
    return parsed


def _nonnegative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(parsed) or parsed < 0 or parsed > 20:
        raise argparse.ArgumentTypeError("must be between 0 and 20")
    return parsed


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a whole number") from exc
    if parsed <= 0 or parsed > 2_000_000:
        raise argparse.ArgumentTypeError("must be between 1 and 2,000,000")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Review a public GitHub pull request diff with Claude Code.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--pr", help="Public GitHub pull request URL")
    source.add_argument("--diff-file", type=Path, help=argparse.SUPPRESS)
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--max-diff-bytes",
        type=_positive_int,
        default=256_000,
        help="Reject larger diffs instead of silently reviewing a partial patch (default: 256000)",
    )
    parser.add_argument(
        "--budget-usd",
        type=_nonnegative_float,
        default=0.50,
        help="Claude Code API spend ceiling for this review (default: 0.50)",
    )
    parser.add_argument(
        "--timeout",
        type=_positive_float,
        default=180,
        help="Maximum Claude Code run time in seconds (default: 180)",
    )
    parser.add_argument(
        "--claude-bin",
        default="claude",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Offer to post the rendered review as a GitHub PR comment after showing it",
    )
    return parser


def _read_diff_file(path: Path, limit: int) -> str:
    try:
        if not path.is_file():
            raise ReviewError("Diff file was not found.")
        with path.open("rb") as source:
            data = source.read(limit + 1)
    except OSError as exc:
        raise ReviewError("Diff file could not be read.") from exc
    if len(data) > limit:
        raise ReviewError(f"Diff file exceeds the {limit:,}-byte limit.")
    try:
        diff = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReviewError("Diff file is not valid UTF-8.") from exc
    if not diff.strip():
        raise ReviewError("Diff file is empty.")
    return diff


def _post_comment(pull_request: PullRequest, markdown: str) -> bool:
    if not sys.stdin.isatty():
        raise ReviewError(
            "Posting requires an interactive terminal so the exact comment can be confirmed."
        )
    print(
        "\nThis will post the review above to the pull request. No comment has been sent yet."
    )
    try:
        answer = input("Post this comment? [y/N] ").strip().lower()
    except EOFError:
        return False
    if answer != "y":
        return False

    gh = shutil.which("gh")
    if not gh:
        raise ReviewError("GitHub CLI (gh) was not found; the review was not posted.")
    payload = json.dumps({"body": markdown}, ensure_ascii=False)
    try:
        result = subprocess.run(
            [
                gh,
                "api",
                pull_request.api_path.replace("/pulls/", "/issues/") + "/comments",
                "--method",
                "POST",
                "--input",
                "-",
            ],
            input=payload,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewError("GitHub CLI could not post the comment.") from exc
    if result.returncode != 0:
        raise ReviewError(
            "GitHub CLI could not post the comment; check gh authentication and permissions."
        )
    return True


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    pull_request: PullRequest | None = None
    pr_url = "local diff"
    try:
        if args.pr:
            pull_request = parse_pull_request_url(args.pr)
            pr_url = pull_request.canonical_url
            diff = fetch_pull_request_diff(pull_request, max_bytes=args.max_diff_bytes)
        else:
            if args.post:
                raise ReviewError(
                    "--post requires --pr; a local diff has no GitHub destination."
                )
            diff = _read_diff_file(args.diff_file, args.max_diff_bytes)

        review = run_claude_review(
            diff,
            pr_url,
            claude_bin=args.claude_bin,
            budget_usd=args.budget_usd,
            timeout_seconds=args.timeout,
        )
        markdown = render_markdown(pr_url, review)
        if args.format == "json":
            print(
                json.dumps(
                    {"pull_request": pr_url, "review": review.as_dict()},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            if args.post:
                print(f"\nComment to post:\n\n{markdown}")
        else:
            print(markdown)

        if args.post:
            assert pull_request is not None
            posted = _post_comment(pull_request, markdown)
            print("Comment posted." if posted else "Not posted.", file=sys.stderr)
        return 0
    except (GitHubError, ReviewError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
