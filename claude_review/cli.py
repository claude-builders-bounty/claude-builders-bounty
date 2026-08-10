"""CLI entrypoint: claude-review --pr <url> [--output review.md]."""

from __future__ import annotations

import argparse
import os
import sys

from .analyzer import review_diff
from .github_client import GitHubClient


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="claude-review",
        description="LLM-powered GitHub PR reviewer (Claude Code sub-agent).",
    )
    p.add_argument("--pr", required=True, help="PR URL, e.g. https://github.com/owner/repo/pull/123")
    p.add_argument("--output", "-o", default="", help="Write review to file (default: stdout)")
    p.add_argument("--diff", default="", help="Local diff file to review instead of fetching from GitHub")
    p.add_argument("--base-url", default="", help="OpenAI-compatible API base URL")
    p.add_argument("--api-key", default="", help="API key (default: DEEPSEEK_API_KEY env)")
    p.add_argument("--model", default="", help="Model name (default: deepseek-chat)")
    args = p.parse_args(argv)

    try:
        if args.diff:
            diff_text = open(args.diff, encoding="utf-8").read()
            pr_url, pr_title = args.pr, ""
        else:
            gh = GitHubClient()
            repo, number = gh.parse_pr_url(args.pr)
            pr = gh.get_pr(repo, number)
            pr_url = pr.get("html_url") or args.pr
            pr_title = pr.get("title", "")
            diff_text = gh.get_diff(repo, number)
            if not diff_text.strip():
                print(f"Empty diff for {repo}#{number} — nothing to review.", file=sys.stderr)
                return 1
    except Exception as e:  # noqa: BLE001
        print(f"Error fetching PR: {e}", file=sys.stderr)
        return 1

    print(f"Reviewing {pr_url} ({len(diff_text)} bytes diff)...", file=sys.stderr)
    result = review_diff(
        diff_text,
        base_url=args.base_url or None,
        api_key=args.api_key or None,
        model=args.model or None,
    )
    md = result.to_markdown(pr_url, pr_title)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(md)
    return 0 if not result.error else 2


if __name__ == "__main__":
    raise SystemExit(main())
