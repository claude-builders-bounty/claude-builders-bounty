import sys
import argparse
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from claude_review import __version__
from claude_review.pr_fetcher import fetch_pr_details, post_pr_comment, parse_pr_url
from claude_review.reviewer import ReviewEngine
from claude_review.formatter import format_review_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Claude Code sub-agent for automated, structured pull request reviews."
    )
    parser.add_argument(
        "--pr",
        dest="pr_url",
        type=str,
        help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)"
    )
    parser.add_argument(
        "--diff-file",
        dest="diff_file",
        type=str,
        help="Optional local unified diff file path (for offline / CI testing)"
    )
    parser.add_argument(
        "--token",
        dest="token",
        type=str,
        default=None,
        help="GitHub Personal Access Token (defaults to GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output_file",
        type=str,
        default=None,
        help="File path to save the generated Markdown review"
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        dest="post_comment",
        help="Post the generated review comment directly to the GitHub PR thread"
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

    if not args.pr_url and not args.diff_file:
        parser.error("Either --pr <URL> or --diff-file <PATH> must be provided.")

    try:
        if args.pr_url:
            print(f"🔍 Fetching pull request data for: {args.pr_url} ...")
            metadata, diff_text = fetch_pr_details(args.pr_url, token=args.token)
        else:
            print(f"📂 Loading local diff from: {args.diff_file} ...")
            with open(args.diff_file, "r", encoding="utf-8") as f:
                diff_text = f.read()
            metadata = {
                "title": os.path.basename(args.diff_file),
                "number": "LOCAL",
                "html_url": "",
                "user": {"login": "local-developer"},
                "base": {"ref": "main"},
                "head": {"ref": "patch"},
            }

        print("🧠 Analyzing changeset and generating structured review ...")
        engine = ReviewEngine()
        review_data = engine.review(metadata, diff_text)
        markdown_output = format_review_markdown(review_data)

        # Output to console
        print("\n" + "=" * 60)
        print(markdown_output)
        print("=" * 60 + "\n")

        # Save to file if requested
        if args.output_file:
            os.makedirs(os.path.dirname(os.path.abspath(args.output_file)), exist_ok=True)
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(markdown_output)
            print(f"💾 Review successfully saved to: {args.output_file}")

        # Post comment to GitHub if requested
        if args.post_comment and args.pr_url:
            print("🚀 Posting review comment to GitHub PR thread ...")
            comment_url = post_pr_comment(args.pr_url, markdown_output, token=args.token)
            print(f"✅ Comment published: {comment_url}")

        return 0

    except Exception as e:
        print(f"❌ Error during PR review execution: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
