"""CLI interface for Claude Review Agent."""

import argparse
import sys
from pathlib import Path

from .agent import PRReviewer
from .formatter import format_review, format_review_compact


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog='claude-review',
        description='Claude Review Agent - Analyze GitHub PRs and generate structured reviews'
    )
    
    parser.add_argument(
        '--pr',
        required=True,
        help='GitHub PR URL to review (e.g., https://github.com/owner/repo/pull/123)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: stdout)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['full', 'compact'],
        default='full',
        help='Output format: full (default) or compact'
    )
    
    parser.add_argument(
        '--post-comment',
        action='store_true',
        help='Post review as a GitHub comment on the PR'
    )
    
    args = parser.parse_args()
    
    # Validate PR URL
    if not args.pr.startswith('https://github.com/'):
        print("Error: PR URL must start with https://github.com/", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Initialize reviewer
        reviewer = PRReviewer()
        
        # Fetch PR data
        print(f"Fetching PR data from: {args.pr}", file=sys.stderr)
        pr_data = reviewer.fetch_pr_data(args.pr)
        
        # Review PR
        print("Analyzing PR...", file=sys.stderr)
        result = reviewer.review(pr_data)
        
        # Format output
        if args.format == 'compact':
            output = format_review_compact(pr_data, result)
        else:
            output = format_review(pr_data, result)
        
        # Output result
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output, encoding='utf-8')
            print(f"Review saved to: {args.output}", file=sys.stderr)
        else:
            print(output)
        
        # Post comment if requested
        if args.post_comment:
            print("Posting review as GitHub comment...", file=sys.stderr)
            post_github_comment(pr_data, output)
            print("Comment posted successfully!", file=sys.stderr)
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def post_github_comment(pr_data, review_text):
    """Post review as a GitHub comment."""
    import subprocess
    
    cmd = [
        'gh', 'pr', 'comment', str(pr_data.number),
        '--repo', pr_data.repo,
        '--body', review_text
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to post comment: {e.stderr}", file=sys.stderr)
        raise


if __name__ == '__main__':
    main()
