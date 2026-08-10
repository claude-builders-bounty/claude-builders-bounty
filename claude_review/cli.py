"""Command-line interface for claude-review."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from . import __version__
from .analyzer import analyze_diff, render_markdown
from .github_client import GitHubError, fetch_pull_request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Claude Code sub-agent that reviews a GitHub PR and posts a structured comment.",
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="PR URL, e.g. https://github.com/owner/repo/pull/123",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write the review to a file instead of stdout.",
    )
    parser.add_argument(
        "--token",
        help="GitHub token (defaults to GITHUB_TOKEN / GH_TOKEN env).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"claude-review {__version__}",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        pr = fetch_pull_request(args.pr, token=args.token)
    except (GitHubError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    result = analyze_diff(pr.diff, pr.changed_files)
    markdown = render_markdown(result, args.pr, pr.title)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        print(f"Review written to {args.output}")
    else:
        print(markdown)

    return 0


if __name__ == "__main__":
    sys.exit(main())