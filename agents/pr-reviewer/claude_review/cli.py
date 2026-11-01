"""
CLI Interface for Claude Code PR Reviewer (`claude-review`).
"""

import argparse
import os
import sys
from .reviewer import ClaudePRReviewer

def main():
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Automated Claude Code agent that analyzes a GitHub PR diff and generates structured Markdown reviews."
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="GitHub Pull Request URL (e.g. https://github.com/owner/repo/pull/123)"
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub Personal Access Token (defaults to GITHUB_TOKEN environment variable)"
    )
    parser.add_argument(
        "--anthropic-key",
        default=os.environ.get("ANTHROPIC_API_KEY"),
        help="Anthropic API Key (defaults to ANTHROPIC_API_KEY environment variable)"
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use (default: claude-sonnet-4-20250514)"
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post the generated review comment directly to the GitHub PR"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write structured Markdown review to a file"
    )

    args = parser.parse_args()

    reviewer = ClaudePRReviewer(
        github_token=args.token,
        anthropic_api_key=args.anthropic_key,
        model=args.model
    )

    try:
        owner, repo, pr_num = reviewer.parse_pr_url(args.pr)
        print(f"🔍 Fetching PR #{pr_num} from {owner}/{repo}...")
        pr_meta, diff_text = reviewer.fetch_pr_data(owner, repo, pr_num)

        title = pr_meta.get("title", f"PR #{pr_num}")
        print(f"🤖 Analyzing diff with Claude ({reviewer.model})...")
        result = reviewer.analyze_diff(owner, repo, pr_num, title, diff_text)

        print("\n" + "=" * 60)
        print(result.markdown_output)
        print("=" * 60 + "\n")

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result.markdown_output)
            print(f"💾 Review written to {args.output}")

        if args.post:
            print("🚀 Posting review comment to GitHub PR...")
            comment_url = reviewer.post_review_comment(owner, repo, pr_num, result.markdown_output)
            print(f"✅ Review posted successfully: {comment_url}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
