"""
Command Line Interface for Claude PR Reviewer.
Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --diff changes.patch --output review.md
    git diff | claude-review --diff -
"""

import sys
import os
import argparse
try:
    from . import __version__
    from .reviewer import ClaudeReviewer
except (ImportError, ValueError):
    try:
        from reviewer import ClaudeReviewer
        __version__ = "1.0.0"
    except ImportError:
        from agents.claude_review.reviewer import ClaudeReviewer
        __version__ = "1.0.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Claude Code sub-agent that reviews a pull request diff and produces structured Markdown feedback."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--pr",
        metavar="URL",
        help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123 or owner/repo#123)"
    )
    group.add_argument(
        "--diff",
        metavar="PATH",
        help="Path to unified diff file, or '-' to read from standard input"
    )

    parser.add_argument(
        "--token",
        metavar="TOKEN",
        help="GitHub personal access token (defaults to GITHUB_TOKEN or GH_TOKEN env vars)"
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "anthropic", "gemini", "openai", "heuristic"],
        default="auto",
        help="LLM provider for review analysis (default: auto)"
    )
    parser.add_argument(
        "--api-key",
        metavar="KEY",
        help="API key for selected provider (defaults to ANTHROPIC_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY)"
    )
    parser.add_argument(
        "--model",
        metavar="NAME",
        help="Override model name (e.g. claude-3-5-sonnet-20241022, gemini-2.5-flash)"
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Save structured markdown review to specified output file"
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post the review comment directly to the PR on GitHub (requires write permissions)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    reviewer = ClaudeReviewer(
        github_token=args.token,
        provider=args.provider,
        api_key=args.api_key,
        model=args.model
    )

    try:
        if args.pr:
            review_md, comment_url = reviewer.review_pr(args.pr, post_comment=args.post)
        elif args.diff:
            if args.diff == "-":
                diff_text = sys.stdin.read()
            else:
                if not os.path.exists(args.diff):
                    sys.stderr.write(f"Error: Diff file not found: {args.diff}\n")
                    return 1
                with open(args.diff, "r", encoding="utf-8", errors="replace") as f:
                    diff_text = f.read()

            review_md = reviewer.review_diff_text(diff_text, title=f"Diff: {args.diff}")
            comment_url = None

        # Output to file if requested
        if args.output:
            out_dir = os.path.dirname(args.output)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(review_md)
            print(f"✅ Review successfully written to {args.output}")

        # Always print to stdout
        print(review_md)

        if comment_url:
            print(f"🚀 Successfully posted review comment to PR: {comment_url}")

        return 0

    except Exception as e:
        sys.stderr.write(f"Error executing claude-review: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
