"""Command line entry point for claude-review."""

from __future__ import annotations

import argparse
import sys

from .github import FetchError, fetch_pull_request, parse_pr_url
from .review import render_review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Review a GitHub pull request with deterministic Claude-style heuristics.",
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub pull request URL, e.g. https://github.com/owner/repo/pull/123",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        ref = parse_pr_url(args.pr)
        pr = fetch_pull_request(ref)
    except (ValueError, FetchError) as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 2

    print(render_review(pr))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
