#!/usr/bin/env python3
"""CLI entry point for claude-review."""

import argparse
import os
import sys

from .reviewer import ClaudeReviewer


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent - Analyze PRs and generate structured review comments."
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Path to write the review Markdown (default: print to stdout)",
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the review as a comment on the PR (requires GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Anthropic model to use (default: claude-sonnet-4-20250514)",
    )

    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    token = os.environ.get("GITHUB_TOKEN")
    if args.post_comment and not token:
        print("Error: GITHUB_TOKEN environment variable is required for --post-comment.", file=sys.stderr)
        sys.exit(1)

    reviewer = ClaudeReviewer(api_key=api_key, model=args.model, github_token=token)

    try:
        review = reviewer.review_pr(args.pr)
    except Exception as e:
        print(f"Error reviewing PR: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"Review written to {args.output}")
    else:
        print(review)

    if args.post_comment:
        reviewer.post_comment(args.pr, review)
        print("Review posted as PR comment.")


if __name__ == "__main__":
    main()