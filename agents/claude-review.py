#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent

Analyzes PR diffs and generates structured Markdown review comments.
Can be used as CLI tool or GitHub Action.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Optional


def get_pr_diff(pr_url: str) -> str:
    """Fetch PR diff using gh CLI."""
    # Extract owner/repo/pr_number from URL
    match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    
    owner, repo, pr_number = match.groups()
    
    # Fetch diff using gh
    result = subprocess.run(
        ['gh', 'pr', 'diff', str(pr_number), '--repo', f'{owner}/{repo}'],
        capture_output=True,
        text=True,
        check=True
    )
    
    return result.stdout


def get_pr_info(pr_url: str) -> dict:
    """Fetch PR metadata using gh CLI."""
    match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    
    owner, repo, pr_number = match.groups()
    
    result = subprocess.run(
        ['gh', 'pr', 'view', str(pr_number), '--repo', f'{owner}/{repo}', '--json', 
         'title,body,author,additions,deletions,changedFiles,files'],
        capture_output=True,
        text=True,
        check=True
    )
    
    return json.loads(result.stdout)


def analyze_diff(diff: str, pr_info: dict) -> dict:
    """
    Analyze PR diff and generate review insights.
    
    Returns structured analysis with:
    - Summary of changes
    - Identified risks
    - Improvement suggestions
    - Confidence score
    """
    # Parse diff statistics
    additions = pr_info.get('additions', 0)
    deletions = pr_info.get('deletions', 0)
    changed_files = pr_info.get('changedFiles', 0)
    files = pr_info.get('files', [])
    
    # Analyze file types
    file_types = {}
    for f in files:
        filename = f.get('path', '')
        ext = os.path.splitext(filename)[1] or 'no-ext'
        file_types[ext] = file_types.get(ext, 0) + 1
    
    # Detect patterns
    risks = []
    suggestions = []
    
    # Check for large changes
    if additions + deletions > 500:
        risks.append("Large PR (>500 lines changed) - consider splitting into smaller PRs for easier review")
    
    # Check for sensitive files
    sensitive_patterns = [
        (r'\.env', 'Environment file changes detected - ensure no secrets are committed'),
        (r'password|secret|key|token', 'Potential credentials in code - verify these are not hardcoded secrets'),
        (r'\.pem$|\.key$', 'Private key files detected - ensure these are not production keys'),
    ]
    
    for pattern, warning in sensitive_patterns:
        if re.search(pattern, diff, re.IGNORECASE):
            risks.append(warning)
    
    # Check for TODO/FIXME comments
    if re.search(r'TODO|FIXME|XXX', diff):
        suggestions.append("Contains TODO/FIXME comments - consider creating issues for tracking")
    
    # Check for test coverage
    has_tests = any('test' in f.get('path', '').lower() for f in files)
    if not has_tests and changed_files > 3:
        suggestions.append("No test files modified - consider adding tests for new functionality")
    
    # Check for documentation
    has_docs = any('readme' in f.get('path', '').lower() or f.get('path', '').endswith('.md') for f in files)
    if not has_docs and additions > 100:
        suggestions.append("Significant code changes without documentation updates")
    
    # Check for breaking changes indicators
    breaking_patterns = [
        r'\bBREAKING\b',
        r'remove[d]?\s+(function|method|class|interface)',
        r'deprecate[d]?',
    ]
    for pattern in breaking_patterns:
        if re.search(pattern, diff, re.IGNORECASE):
            risks.append("Potential breaking changes detected - update version and changelog")
            break
    
    # Determine confidence based on analysis
    risk_count = len(risks)
    if risk_count == 0:
        confidence = "High"
    elif risk_count <= 2:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    # Generate summary
    summary_parts = [
        f"This PR modifies {changed_files} file(s) with {additions} additions and {deletions} deletions.",
    ]
    
    if file_types:
        main_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:3]
        type_str = ", ".join([f"{ext} ({count})" for ext, count in main_types])
        summary_parts.append(f"Primary file types: {type_str}.")
    
    summary_parts.append(f"Author: {pr_info.get('author', {}).get('login', 'unknown')}.")
    
    summary = " ".join(summary_parts)
    
    return {
        'summary': summary,
        'risks': risks,
        'suggestions': suggestions,
        'confidence': confidence,
        'stats': {
            'additions': additions,
            'deletions': deletions,
            'changed_files': changed_files,
            'file_types': file_types
        }
    }


def generate_markdown_review(analysis: dict) -> str:
    """Generate structured Markdown review comment."""
    lines = []
    
    # Header
    lines.append("## 🔍 PR Review")
    lines.append("")
    
    # Summary
    lines.append("### 📋 Summary")
    lines.append(analysis['summary'])
    lines.append("")
    
    # Risks
    if analysis['risks']:
        lines.append("### ⚠️ Identified Risks")
        for risk in analysis['risks']:
            lines.append(f"- {risk}")
        lines.append("")
    
    # Suggestions
    if analysis['suggestions']:
        lines.append("### 💡 Improvement Suggestions")
        for suggestion in analysis['suggestions']:
            lines.append(f"- {suggestion}")
        lines.append("")
    
    # Confidence
    confidence_emoji = {
        'High': '🟢',
        'Medium': '🟡',
        'Low': '🔴'
    }
    emoji = confidence_emoji.get(analysis['confidence'], '⚪')
    lines.append("### 📊 Confidence Score")
    lines.append(f"{emoji} **{analysis['confidence']}**")
    lines.append("")
    
    # Stats
    stats = analysis['stats']
    lines.append("### 📈 Statistics")
    lines.append(f"- **Additions:** {stats['additions']}")
    lines.append(f"- **Deletions:** {stats['deletions']}")
    lines.append(f"- **Changed Files:** {stats['changed_files']}")
    lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("*Generated by Claude Code PR Reviewer Agent*")
    
    return "\n".join(lines)


def post_comment(pr_url: str, comment: str) -> None:
    """Post review comment to PR."""
    match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    
    owner, repo, pr_number = match.groups()
    
    # Write comment to temp file to avoid shell escaping issues
    with open('/tmp/pr_review_comment.md', 'w') as f:
        f.write(comment)
    
    subprocess.run(
        ['gh', 'pr', 'comment', str(pr_number), '--repo', f'{owner}/{repo}', 
         '--body-file', '/tmp/pr_review_comment.md'],
        check=True
    )


def main():
    parser = argparse.ArgumentParser(description='Claude Code PR Reviewer Agent')
    parser.add_argument('--pr', required=True, help='PR URL (e.g., https://github.com/owner/repo/pull/123)')
    parser.add_argument('--post', action='store_true', help='Post review comment to PR')
    parser.add_argument('--json', action='store_true', help='Output analysis as JSON')
    
    args = parser.parse_args()
    
    try:
        # Fetch PR data
        print(f"Fetching PR: {args.pr}", file=sys.stderr)
        diff = get_pr_diff(args.pr)
        pr_info = get_pr_info(args.pr)
        
        # Analyze
        print("Analyzing diff...", file=sys.stderr)
        analysis = analyze_diff(diff, pr_info)
        
        # Output
        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            review = generate_markdown_review(analysis)
            print(review)
            
            if args.post:
                print("Posting comment to PR...", file=sys.stderr)
                post_comment(args.pr, review)
                print("✓ Comment posted successfully", file=sys.stderr)
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing gh command: {e}", file=sys.stderr)
        print(f"stdout: {e.stdout}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
