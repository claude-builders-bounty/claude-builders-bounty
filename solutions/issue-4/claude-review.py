#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent

A sub-agent that analyzes GitHub PR diffs and posts structured review comments.

Usage:
    python claude-review.py --pr https://github.com/owner/repo/pull/123
    python claude-review.py --pr 123 --repo owner/repo

Author: disillusi0n
Bounty: $150 (Issue #4)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class PRReview:
    """Structured PR review output."""
    summary: str
    risks: List[str]
    suggestions: List[str]
    confidence: str  # "Low", "Medium", "High"

def fetch_pr_diff(pr_url: str, github_token: Optional[str] = None) -> str:
    """
    Fetch PR diff from GitHub.
    
    Args:
        pr_url: Full PR URL or PR number with repo
        github_token: Optional GitHub token for private repos
    
    Returns:
        Diff text
    """
    import subprocess
    
    # Parse PR URL
    if pr_url.startswith("https://"):
        # Full URL: https://github.com/owner/repo/pull/123
        parts = pr_url.split("/")
        owner = parts[3]
        repo = parts[4]
        pr_number = parts[6]
    else:
        raise ValueError("Invalid PR URL format. Use: https://github.com/owner/repo/pull/123")
    
    # Fetch diff using GitHub API
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    
    headers = ["Accept: application/vnd.github.v3.diff"]
    if github_token:
        headers.append(f"Authorization: Bearer {github_token}")
    
    curl_cmd = [
        "curl", "-s",
        "-H", "Accept: application/vnd.github.v3.diff",
    ]
    
    if github_token:
        curl_cmd.extend(["-H", f"Authorization: Bearer {github_token}"])
    
    curl_cmd.append(api_url)
    
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR diff: {result.stderr}")
    
    return result.stdout

def analyze_diff(diff_text: str) -> PRReview:
    """
    Analyze PR diff and generate review.
    
    This is a template - integrate with Claude API for real analysis.
    
    Args:
        diff_text: The PR diff text
    
    Returns:
        Structured review
    """
    # Parse diff to understand changes
    files_changed = []
    additions = 0
    deletions = 0
    
    current_file = None
    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            current_file = line.split(" ")[2].replace("a/", "")
            files_changed.append(current_file)
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    
    # Generate review (this is where you'd call Claude API)
    # For now, return a template review
    
    summary = f"This PR modifies {len(files_changed)} file(s) with {additions} additions and {deletions} deletions."
    
    risks = []
    if "password" in diff_text.lower() or "secret" in diff_text.lower():
        risks.append("⚠️ Possible sensitive data exposure (password/secret detected in diff)")
    if "sql" in diff_text.lower() and ("+" in diff_text or "-" in diff_text):
        risks.append("⚠️ SQL-related changes detected - review for SQL injection risks")
    if "eval(" in diff_text or "exec(" in diff_text:
        risks.append("⚠️ Dynamic code execution detected - security risk")
    if additions > 500:
        risks.append("⚠️ Large PR (>500 lines) - consider splitting into smaller PRs")
    
    suggestions = []
    if "TODO" in diff_text or "FIXME" in diff_text:
        suggestions.append("💡 Consider resolving TODO/FIXME comments before merging")
    if "console.log" in diff_text:
        suggestions.append("💡 Remove debug console.log statements")
    if "test" not in str(files_changed).lower() and additions > 100:
        suggestions.append("💡 Consider adding tests for new functionality")
    
    # Determine confidence based on diff size and content
    if additions + deletions < 100:
        confidence = "High"
    elif additions + deletions < 500:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    return PRReview(
        summary=summary,
        risks=risks if risks else ["No significant risks identified"],
        suggestions=suggestions if suggestions else ["No specific suggestions"],
        confidence=confidence
    )

def format_review_markdown(review: PRReview, pr_url: str) -> str:
    """
    Format review as structured Markdown.
    
    Args:
        review: The review object
        pr_url: PR URL for reference
    
    Returns:
        Formatted Markdown string
    """
    md = f"""# 🤖 Claude Code PR Review

**PR:** {pr_url}

---

## 📝 Summary

{review.summary}

---

## ⚠️ Identified Risks

"""
    for risk in review.risks:
        md += f"- {risk}\n"
    
    md += """
---

## 💡 Improvement Suggestions

"""
    for suggestion in review.suggestions:
        md += f"- {suggestion}\n"
    
    md += f"""
---

## 🎯 Confidence Score

**{review.confidence}**

---

*This review was generated by Claude Code. Please review carefully before merging.*
"""
    
    return md

def post_review_comment(pr_url: str, comment: str, github_token: str) -> Dict:
    """
    Post review comment to GitHub PR.
    
    Args:
        pr_url: PR URL
        comment: Markdown comment
        github_token: GitHub token with repo scope
    
    Returns:
        API response
    """
    import subprocess
    
    # Parse PR URL
    parts = pr_url.split("/")
    owner = parts[3]
    repo = parts[4]
    pr_number = parts[6]
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    
    # Prepare comment data
    data = json.dumps({"body": comment})
    
    # Post comment using curl
    curl_cmd = [
        "curl", "-s", "-X", "POST",
        "-H", "Accept: application/vnd.github+json",
        "-H", f"Authorization: Bearer {github_token}",
        "-H", "Content-Type: application/json",
        "-d", data,
        api_url
    ]
    
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to post comment: {result.stderr}")
    
    return json.loads(result.stdout)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Claude Code PR Reviewer - Analyze and review GitHub PRs"
    )
    parser.add_argument(
        "--pr",
        required=True,
        help="PR URL (https://github.com/owner/repo/pull/123)"
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post review as comment to PR"
    )
    parser.add_argument(
        "--output",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    try:
        # Fetch PR diff
        print(f"Fetching PR diff from {args.pr}...", file=sys.stderr)
        diff_text = fetch_pr_diff(args.pr, args.token)
        
        # Analyze diff
        print("Analyzing changes...", file=sys.stderr)
        review = analyze_diff(diff_text)
        
        # Format output
        if args.output == "markdown":
            output = format_review_markdown(review, args.pr)
        else:
            output = json.dumps({
                "summary": review.summary,
                "risks": review.risks,
                "suggestions": review.suggestions,
                "confidence": review.confidence
            }, indent=2)
        
        # Output or post
        if args.post:
            if not args.token:
                raise ValueError("GitHub token required for posting comments")
            
            print("Posting review comment...", file=sys.stderr)
            result = post_review_comment(args.pr, output, args.token)
            print(f"✅ Comment posted: {result.get('html_url', 'success')}", file=sys.stderr)
        else:
            print(output)
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
