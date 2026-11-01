"""CLI entry point: claude-review --pr <url>"""

from __future__ import annotations

import argparse
import os
import sys

from claude_review.reviewer import fetch_pr, review, parse_pr_url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="claude-review", description="Review a GitHub PR and print a structured Markdown review.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--token", default=None, help="GitHub token (default: GITHUB_TOKEN env)")
    parser.add_argument("--llm", action="store_true", help="Use LLM-enhanced review if an API key is available")
    parser.add_argument("--output", default=None, help="Write review to file instead of stdout")
    args = parser.parse_args(argv)

    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("RADAR_GITHUB_TOKEN")
    try:
        pr = fetch_pr(args.pr, token)
    except Exception as exc:
        print(f"error fetching PR: {exc}", file=sys.stderr)
        return 1
    out = review(pr, use_llm=args.llm)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
        print(f"wrote {args.output}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
