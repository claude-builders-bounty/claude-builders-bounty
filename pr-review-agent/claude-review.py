#!/usr/bin/env python3
"""
Claude Code agent that reviews a PR and posts a structured comment.

Usage:
    python3 claude-review.py --pr https://github.com/owner/repo/pull/123

Requirements:
    - GitHub CLI (gh) installed and authenticated
    - Python 3.8+
"""

import argparse
import json
import subprocess
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class Confidence(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@dataclass
class ReviewResult:
    summary: str
    risks: List[str]
    suggestions: List[str]
    confidence: Confidence


def get_pr_info(pr_url: str) -> Tuple[str, str, str, str]:
    """Extract owner, repo, and PR number from URL."""
    # Parse URL: https://github.com/owner/repo/pull/123
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    
    owner, repo, pr_number = match.groups()
    return owner, repo, pr_number, f"{owner}/{repo}"


def fetch_pr_diff(owner: str, repo: str, pr_number: str) -> str:
    """Fetch the PR diff using GitHub CLI."""
    cmd = ["D:\\dev\\tools\\gh\\bin\\gh.exe", "pr", "diff", pr_number, "--repo", f"{owner}/{repo}"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR diff: {result.stderr}")
    return result.stdout


def fetch_pr_details(owner: str, repo: str, pr_number: str) -> Dict:
    """Fetch PR details using GitHub CLI."""
    cmd = ["D:\\dev\\tools\\gh\\bin\\gh.exe", "pr", "view", pr_number, "--repo", f"{owner}/{repo}", "--json", "title,body,author,files,additions,deletions"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR details: {result.stderr}")
    return json.loads(result.stdout)


def analyze_diff(diff: str, details: Dict) -> ReviewResult:
    """Analyze the PR diff and generate a review."""
    lines = diff.split('\n')
    
    # Categorize changes
    added_files = []
    removed_files = []
    modified_files = []
    
    current_file = None
    additions = 0
    deletions = 0
    
    for line in lines:
        if line.startswith('diff --git'):
            # Extract filename
            match = re.search(r'b/(.+)$', line)
            if match:
                current_file = match.group(1)
        elif line.startswith('+') and not line.startswith('+++'):
            additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1
    
    # Analyze risks
    risks = []
    suggestions = []
    
    # Check for large changes
    total_changes = additions + deletions
    if total_changes > 500:
        risks.append("Large PR with many changes - may be difficult to review thoroughly")
    
    # Check for security-related patterns
    diff_lower = diff.lower()
    
    if 'password' in diff_lower or 'secret' in diff_lower or 'token' in diff_lower:
        risks.append("Potential security concern - changes involve sensitive data")
    
    if 'sql' in diff_lower and ('delete' in diff_lower or 'drop' in diff_lower):
        risks.append("Database operations detected - verify data integrity")
    
    if 'eval(' in diff or 'exec(' in diff:
        risks.append("Dynamic code execution detected - potential security risk")
    
    if 'import os' in diff or 'subprocess' in diff:
        risks.append("System command execution detected - review for security")
    
    # Check for testing
    if 'test' not in diff_lower and 'spec' not in diff_lower:
        suggestions.append("Consider adding tests for new functionality")
    
    # Check for documentation
    if 'readme' not in diff_lower and 'doc' not in diff_lower:
        suggestions.append("Update documentation if this changes public API")
    
    # Check for error handling
    if 'try' not in diff and 'catch' not in diff and 'except' not in diff:
        suggestions.append("Consider adding error handling for edge cases")
    
    # Generate summary
    summary_parts = []
    if additions > 0:
        summary_parts.append(f"adds {additions} lines")
    if deletions > 0:
        summary_parts.append(f"removes {deletions} lines")
    
    summary = f"This PR {', '.join(summary_parts)}. "
    
    if risks:
        summary += f"Identified {len(risks)} potential risk(s). "
    
    if suggestions:
        summary += f"Has {len(suggestions)} suggestion(s) for improvement."
    
    # Determine confidence
    confidence = Confidence.HIGH
    if total_changes > 1000:
        confidence = Confidence.MEDIUM
    if total_changes > 2000:
        confidence = Confidence.LOW
    
    return ReviewResult(
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence
    )


def format_review(review: ReviewResult) -> str:
    """Format the review as Markdown."""
    md = []
    md.append("## PR Review")
    md.append("")
    md.append("### Summary")
    md.append(review.summary)
    md.append("")
    
    if review.risks:
        md.append("### Identified Risks")
        for risk in review.risks:
            md.append(f"- {risk}")
        md.append("")
    
    if review.suggestions:
        md.append("### Improvement Suggestions")
        for suggestion in review.suggestions:
            md.append(f"- {suggestion}")
        md.append("")
    
    md.append(f"### Confidence Score: **{review.confidence.value}**")
    md.append("")
    md.append("---")
    md.append("*Generated by claude-review agent*")
    
    return "\n".join(md)


def post_comment(owner: str, repo: str, pr_number: str, comment: str) -> bool:
    """Post a comment on the PR."""
    cmd = ["D:\\dev\\tools\\gh\\bin\\gh.exe", "pr", "comment", pr_number, "--repo", f"{owner}/{repo}", "--body", comment]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Review a GitHub PR")
    parser.add_argument("--pr", required=True, help="PR URL (https://github.com/owner/repo/pull/123)")
    parser.add_argument("--post", action="store_true", help="Post the review as a comment")
    parser.add_argument("--output", help="Save review to file")
    
    args = parser.parse_args()
    
    try:
        # Parse PR URL
        owner, repo, pr_number, full_name = get_pr_info(args.pr)
        print(f"Reviewing PR #{pr_number} in {full_name}...")
        
        # Fetch PR details and diff
        details = fetch_pr_details(owner, repo, pr_number)
        diff = fetch_pr_diff(owner, repo, pr_number)
        
        print(f"Title: {details['title']}")
        print(f"Changes: +{details['additions']} -{details['deletions']}")
        
        # Analyze and generate review
        review = analyze_diff(diff, details)
        formatted_review = format_review(review)
        
        # Print review
        print("\n" + formatted_review)
        
        # Save to file if requested
        if args.output:
            Path(args.output).write_text(formatted_review)
            print(f"\nReview saved to {args.output}")
        
        # Post comment if requested
        if args.post:
            if post_comment(owner, repo, pr_number, formatted_review):
                print("\n✅ Review posted successfully!")
            else:
                print("\n❌ Failed to post review")
                sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
