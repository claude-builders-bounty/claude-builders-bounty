#!/usr/bin/env python3
"""
CLI entrypoint for Claude Review Agent:
claude-review --pr https://github.com/owner/repo/pull/123
"""
import sys
import os
import argparse
from typing import Dict, Any

from claude_review.github_client import GitHubClient
from claude_review.analyzer import DiffAnalyzer

def main():
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Claude Code sub-agent that reviews a pull request diff and outputs a structured Markdown review comment."
    )
    parser.add_argument(
        "--pr",
        dest="pr_url",
        type=str,
        help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123) or shorthand owner/repo#123"
    )
    parser.add_argument(
        "--diff-file",
        dest="diff_file",
        type=str,
        help="Optional local path to unified diff file (useful for offline testing or git pre-push hooks)"
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output_file",
        type=str,
        help="Optional path to write generated Markdown review"
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Automatically post the generated review as a comment to the GitHub PR (requires GITHUB_TOKEN)"
    )
    parser.add_argument(
        "--github-token",
        dest="github_token",
        type=str,
        help="GitHub Personal Access Token (defaults to GITHUB_TOKEN environment variable)"
    )
    parser.add_argument(
        "--anthropic-api-key",
        dest="anthropic_api_key",
        type=str,
        help="Anthropic API Key for Claude LLM inference (defaults to ANTHROPIC_API_KEY environment variable)"
    )
    parser.add_argument(
        "--model",
        dest="model",
        type=str,
        default="claude-3-5-sonnet-20241022",
        help="Anthropic Claude model (default: claude-3-5-sonnet-20241022)"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress banner and auxiliary logs; only output review markdown to stdout"
    )

    args = parser.parse_args()

    if not args.pr_url and not args.diff_file:
        parser.error("You must specify either --pr <URL> or --diff-file <PATH>.")

    gh_client = GitHubClient(token=args.github_token)
    analyzer = DiffAnalyzer(anthropic_api_key=args.anthropic_api_key, model=args.model)

    pr_meta: Dict[str, Any] = {}
    diff_text = ""

    if args.pr_url:
        try:
            owner, repo, pr_number = gh_client.parse_pr_url(args.pr_url)
            if not args.quiet:
                print(f"🔍 [Claude Review] Fetching PR metadata for {owner}/{repo}#{pr_number}...", file=sys.stderr)
            pr_meta = gh_client.get_pr_metadata(owner, repo, pr_number)
            
            if not args.quiet:
                print(f"📥 [Claude Review] Fetching unified diff...", file=sys.stderr)
            diff_text = gh_client.get_pr_diff(owner, repo, pr_number)
        except Exception as e:
            print(f"❌ Error fetching PR details: {e}", file=sys.stderr)
            sys.exit(1)

    if args.diff_file:
        try:
            with open(args.diff_file, "r", encoding="utf-8", errors="replace") as f:
                diff_text = f.read()
            if not pr_meta:
                pr_meta = {
                    "owner": "local",
                    "repo": "workspace",
                    "number": 0,
                    "title": os.path.basename(args.diff_file),
                    "author": "developer",
                    "base_branch": "main",
                    "head_branch": "feature",
                    "body": f"Local diff file analysis: {args.diff_file}"
                }
        except Exception as e:
            print(f"❌ Error reading diff file: {e}", file=sys.stderr)
            sys.exit(1)

    if not diff_text or not diff_text.strip():
        print("⚠️ Warning: Empty diff received. Nothing to review.", file=sys.stderr)
        sys.exit(0)

    if not args.quiet:
        print(f"🤖 [Claude Review] Analyzing diff ({len(diff_text.splitlines())} lines)...", file=sys.stderr)

    review_md = analyzer.analyze(pr_meta, diff_text)

    # Print review
    print(review_md)

    # Save to file if requested
    if args.output_file:
        try:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(review_md)
            if not args.quiet:
                print(f"💾 Saved review to {args.output_file}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Failed to save review output: {e}", file=sys.stderr)

    # Post comment to PR if requested
    if args.post_comment and args.pr_url:
        try:
            owner, repo, pr_number = gh_client.parse_pr_url(args.pr_url)
            if not args.quiet:
                print(f"🚀 [Claude Review] Posting review comment to PR #{pr_number}...", file=sys.stderr)
            comment_url = gh_client.post_pr_comment(owner, repo, pr_number, review_md)
            if not args.quiet:
                print(f"✅ Comment posted successfully: {comment_url}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Failed to post comment to PR: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
