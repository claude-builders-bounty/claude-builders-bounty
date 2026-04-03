#!/usr/bin/env python3
"""
claude-review - A Claude Code sub-agent for PR review

This CLI tool analyzes GitHub PR diffs and generates structured Markdown reviews.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md

Environment Variables:
    ANTHROPIC_API_KEY - Required for Claude API access
    GITHUB_TOKEN - Optional, for private repos (uses public API otherwise)
"""

import argparse
import json
import os
import re
import sys
from typing import Optional
from urllib.parse import urlparse

import requests


# Configuration
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-20250514"


def get_env_or_exit(var_name: str) -> str:
    """Get environment variable or exit with error."""
    value = os.getenv(var_name)
    if not value:
        print(f"Error: {var_name} environment variable is required", file=sys.stderr)
        sys.exit(1)
    return value


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse GitHub PR URL into (owner, repo, pr_number)."""
    # Handle various GitHub URL formats
    patterns = [
        r"github\.com/([^/]+)/([^/]+)/pull/(\d+)",
        r"github\.com/([^/]+)/([^/]+)/pulls/(\d+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner, repo, pr_number = match.groups()
            return owner, repo, int(pr_number)
    
    # Try URL parsing as fallback
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    
    if len(path_parts) >= 4 and path_parts[2] == "pull":
        return path_parts[0], path_parts[1], int(path_parts[3])
    
    raise ValueError(f"Could not parse PR URL: {url}")


def fetch_pr_info(owner: str, repo: str, pr_number: int, token: Optional[str] = None) -> dict:
    """Fetch PR information from GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: Optional[str] = None) -> str:
    """Fetch PR diff from GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3.diff"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def fetch_pr_files(owner: str, repo: str, pr_number: int, token: Optional[str] = None) -> list:
    """Fetch list of changed files in PR."""
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def truncate_diff(diff: str, max_chars: int = 100000) -> str:
    """Truncate diff if too large for API."""
    if len(diff) <= max_chars:
        return diff
    
    # Try to truncate at a sensible boundary
    truncated = diff[:max_chars]
    last_newline = truncated.rfind("\n")
    if last_newline > 0:
        truncated = truncated[:last_newline]
    
    return truncated + "\n\n... [diff truncated due to size] ..."


def analyze_with_claude(
    pr_info: dict,
    diff: str,
    files: list,
    api_key: str
) -> dict:
    """Send PR data to Claude API for analysis."""
    
    # Build the prompt
    file_summary = "\n".join([
        f"- {f['filename']} ({f['status']}: +{f.get('additions', 0)}/-{f.get('deletions', 0)})"
        for f in files[:20]  # Limit file list
    ])
    
    if len(files) > 20:
        file_summary += f"\n- ... and {len(files) - 20} more files"
    
    prompt = f"""Please review this pull request and provide a structured analysis.

PR TITLE: {pr_info.get('title', 'N/A')}
PR DESCRIPTION:
{pr_info.get('body', 'No description provided')}

FILES CHANGED ({len(files)} total):
{file_summary}

DIFF:
```diff
{truncate_diff(diff)}
```

Provide your review in this exact format:

## Summary
[2-3 sentences summarizing what this PR does and its impact]

## Identified Risks
- [Risk 1: description of potential issue]
- [Risk 2: description of potential issue]
- [etc.]

## Improvement Suggestions
- [Suggestion 1: specific actionable recommendation]
- [Suggestion 2: specific actionable recommendation]
- [etc.]

## Confidence Score
[Low / Medium / High]

Reasoning for confidence score: [1-2 sentences explaining your confidence level]
"""
    
    # Call Claude API
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    content = result["content"][0]["text"]
    
    # Parse the response
    return parse_claude_response(content)


def parse_claude_response(content: str) -> dict:
    """Parse Claude's response into structured format."""
    # Extract sections using regex
    summary_match = re.search(r'## Summary\s*\n(.*?)(?=##|\Z)', content, re.DOTALL)
    risks_match = re.search(r'## Identified Risks\s*\n(.*?)(?=##|\Z)', content, re.DOTALL)
    suggestions_match = re.search(r'## Improvement Suggestions\s*\n(.*?)(?=##|\Z)', content, re.DOTALL)
    confidence_match = re.search(r'## Confidence Score\s*\n(.*?)(?=\n|$)', content, re.DOTALL)
    
    def parse_list(text: str) -> list:
        """Parse markdown list into array."""
        if not text:
            return []
        items = re.findall(r'^[-*]\s*(.+)$', text.strip(), re.MULTILINE)
        return [item.strip() for item in items if item.strip()]
    
    def parse_confidence(text: str) -> str:
        """Extract confidence level."""
        if not text:
            return "Medium"
        text_lower = text.lower()
        if "high" in text_lower:
            return "High"
        elif "low" in text_lower:
            return "Low"
        return "Medium"
    
    return {
        "summary": summary_match.group(1).strip() if summary_match else "Summary not provided",
        "risks": parse_list(risks_match.group(1)) if risks_match else [],
        "suggestions": parse_list(suggestions_match.group(1)) if suggestions_match else [],
        "confidence": parse_confidence(confidence_match.group(1)) if confidence_match else "Medium",
        "raw_response": content
    }


def format_review_markdown(review: dict, pr_url: str, pr_info: dict) -> str:
    """Format review as Markdown."""
    confidence_emoji = {
        "High": "🟢",
        "Medium": "🟡",
        "Low": "🔴"
    }.get(review["confidence"], "⚪")
    
    markdown = f"""# 🔍 PR Review Report

**PR:** [{pr_info.get('title', 'Untitled')}]({pr_url})  
**Author:** @{pr_info.get('user', {}).get('login', 'unknown')}  
**Reviewed:** Generated by Claude Code

---

## 📋 Summary

{review['summary']}

---

## ⚠️ Identified Risks

"""
    
    if review["risks"]:
        for risk in review["risks"]:
            markdown += f"- {risk}\n"
    else:
        markdown += "_No significant risks identified._\n"
    
    markdown += "\n---\n\n## 💡 Improvement Suggestions\n\n"
    
    if review["suggestions"]:
        for suggestion in review["suggestions"]:
            markdown += f"- {suggestion}\n"
    else:
        markdown += "_No suggestions at this time._\n"
    
    markdown += f"""
---

## 🎯 Confidence Score

{confidence_emoji} **{review['confidence']}**

---

*This review was generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty) - a Claude Code sub-agent for automated PR analysis.*
"""
    
    return markdown


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate AI-powered PR reviews using Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
    claude-review --pr URL --json
        """
    )
    
    parser.add_argument(
        "--pr", "-p",
        required=True,
        help="GitHub PR URL to review"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: print to stdout)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON instead of Markdown"
    )
    parser.add_argument(
        "--github-token",
        help="GitHub token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--claude-api-key",
        help="Claude API key (or set ANTHROPIC_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    # Get credentials
    claude_api_key = args.claude_api_key or get_env_or_exit("ANTHROPIC_API_KEY")
    github_token = args.github_token or os.getenv("GITHUB_TOKEN")
    
    # Parse PR URL
    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
        print(f"📎 Analyzing PR: {owner}/{repo}#{pr_number}", file=sys.stderr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Fetch PR data
    try:
        print("📥 Fetching PR information...", file=sys.stderr)
        pr_info = fetch_pr_info(owner, repo, pr_number, github_token)
        
        print("📥 Fetching PR diff...", file=sys.stderr)
        diff = fetch_pr_diff(owner, repo, pr_number, github_token)
        
        print("📥 Fetching changed files...", file=sys.stderr)
        files = fetch_pr_files(owner, repo, pr_number, github_token)
        
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            print("Error: PR not found or not accessible", file=sys.stderr)
        elif e.response.status_code == 403:
            print("Error: API rate limit exceeded or authentication required", file=sys.stderr)
        else:
            print(f"Error fetching PR data: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Analyze with Claude
    try:
        print("🤖 Analyzing with Claude...", file=sys.stderr)
        review = analyze_with_claude(pr_info, diff, files, claude_api_key)
    except requests.HTTPError as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Output results
    if args.json:
        output = json.dumps(review, indent=2)
    else:
        output = format_review_markdown(review, args.pr, pr_info)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"✅ Review saved to: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
