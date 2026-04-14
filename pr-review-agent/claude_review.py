#!/usr/bin/env python3
"""
Claude Code PR Review Agent
Bounty: claude-builders-bounty/claude-builders-bounty #4
Author: FanLi (范蠡)
"""

import argparse
import sys
import os
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

from github_client import GitHubClient
from claude_client import ClaudeClient
from review_formatter import format_review_markdown


def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    """
    Parse GitHub PR URL to extract owner, repo, and PR number.
    
    Args:
        pr_url: GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)
        
    Returns:
        Tuple of (owner, repo, pr_number)
        
    Raises:
        ValueError: If URL is invalid
    """
    try:
        parsed = urlparse(pr_url)
        if parsed.netloc != "github.com":
            raise ValueError("URL must be a GitHub URL")
            
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 4 or path_parts[2] != "pull":
            raise ValueError("URL must be a GitHub PR URL")
            
        owner = path_parts[0]
        repo = path_parts[1]
        pr_number = int(path_parts[3])
        
        return owner, repo, pr_number
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid PR URL format: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent - Analyze PR diffs and generate structured reviews",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
        """
    )
    
    parser.add_argument(
        "--pr", 
        required=True,
        help="GitHub PR URL to analyze"
    )
    
    parser.add_argument(
        "--output",
        help="Output file path (default: stdout)"
    )
    
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token for API access (default: GITHUB_TOKEN env var)"
    )
    
    parser.add_argument(
        "--claude-key",
        default=os.environ.get("CLAUDE_API_KEY"),
        help="Claude API key (default: CLAUDE_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    # Validate required tokens
    if not args.github_token:
        print("Error: GitHub token required. Set GITHUB_TOKEN env var or use --github-token", file=sys.stderr)
        sys.exit(1)
        
    if not args.claude_key:
        print("Error: Claude API key required. Set CLAUDE_API_KEY env var or use --claude-key", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Parse PR URL
        owner, repo, pr_number = parse_pr_url(args.pr)
        print(f"Analyzing PR #{pr_number} in {owner}/{repo}...")
        
        # Initialize clients
        github_client = GitHubClient(args.github_token)
        claude_client = ClaudeClient(args.claude_key)
        
        # Get PR details and diff
        pr_details = github_client.get_pr_details(owner, repo, pr_number)
        pr_diff = github_client.get_pr_diff(owner, repo, pr_number)
        
        print(f"PR Title: {pr_details['title']}")
        print(f"Files changed: {len(pr_diff.split('diff --git')) - 1}")
        
        # Analyze with Claude
        print("Analyzing with Claude AI...")
        review_data = claude_client.analyze_pr_diff(pr_diff, pr_details)
        
        # Format output
        markdown_review = format_review_markdown(review_data)
        
        # Output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(markdown_review)
            print(f"Review saved to {args.output}")
        else:
            print("\n" + "="*60)
            print(markdown_review)
            print("="*60)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()