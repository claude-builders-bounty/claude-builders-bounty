#!/usr/bin/env python3
"""
Claude Code PR Review Agent
============================

Automated PR review using Claude Code sub-agent capabilities.
Analyzes PR diffs and generates structured review comments.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr owner/repo#123
    claude-review --diff diff.txt

Author: Claude Code Agent
License: MIT
Version: 1.0.0
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
from pathlib import Path


@dataclass
class ReviewResult:
    """Structured review result."""
    summary: str
    risks: List[str]
    suggestions: List[str]
    confidence: str  # Low / Medium / High
    files_changed: int
    lines_added: int
    lines_deleted: int
    files: List[Dict[str, any]]


def parse_pr_url(url: str) -> tuple:
    """Parse GitHub PR URL into owner, repo, number."""
    # Handle different URL formats
    patterns = [
        r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)',
        r'https://github\.com/([^/]+)/([^/]+)/issues/(\d+)',
        r'^([^/]+)/([^#]+)#(\d+)$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return match.groups()
    
    raise ValueError(f"Invalid PR URL format: {url}")


def get_pr_diff(owner: str, repo: str, pr_number: str) -> str:
    """Fetch PR diff using gh CLI."""
    try:
        result = subprocess.run(
            ['gh', 'pr', 'diff', pr_number, '--repo', f'{owner}/{repo}'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching PR diff: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def get_pr_info(owner: str, repo: str, pr_number: str) -> dict:
    """Fetch PR metadata using gh CLI."""
    try:
        result = subprocess.run(
            ['gh', 'pr', 'view', pr_number, '--repo', f'{owner}/{repo}', '--json',
             'title,body,author,files,additions,deletions,changedFiles'],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching PR info: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def analyze_diff(diff: str, pr_info: dict) -> ReviewResult:
    """Analyze PR diff and generate review."""
    
    # Extract statistics
    lines = diff.split('\n')
    files_changed = pr_info.get('changedFiles', 0)
    lines_added = pr_info.get('additions', 0)
    lines_deleted = pr_info.get('deletions', 0)
    
    # Analyze files
    files = []
    for file_info in pr_info.get('files', []):
        files.append({
            'path': file_info.get('path', ''),
            'additions': file_info.get('additions', 0),
            'deletions': file_info.get('deletions', 0)
        })
    
    # Generate summary
    summary = generate_summary(diff, pr_info, files_changed, lines_added, lines_deleted)
    
    # Identify risks
    risks = identify_risks(diff, files)
    
    # Generate suggestions
    suggestions = generate_suggestions(diff, files, risks)
    
    # Calculate confidence
    confidence = calculate_confidence(files_changed, lines_added, lines_deleted, len(risks))
    
    return ReviewResult(
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
        files_changed=files_changed,
        lines_added=lines_added,
        lines_deleted=lines_deleted,
        files=files
    )


def generate_summary(diff: str, pr_info: dict, files: int, added: int, deleted: int) -> str:
    """Generate 2-3 sentence summary of changes."""
    title = pr_info.get('title', 'Untitled PR')
    
    # Count file types
    file_extensions = {}
    for file_info in pr_info.get('files', []):
        path = file_info.get('path', '')
        ext = Path(path).suffix or 'no extension'
        file_extensions[ext] = file_extensions.get(ext, 0) + 1
    
    # Most common file type
    common_type = max(file_extensions.items(), key=lambda x: x[1])[0] if file_extensions else 'unknown'
    
    summary = f"This PR \"{title}\" modifies {files} files "
    summary += f"(+{added} -{deleted} lines). "
    summary += f"Primary changes are in {common_type} files."
    
    return summary


def identify_risks(diff: str, files: List[Dict]) -> List[str]:
    """Identify potential risks in the PR."""
    risks = []
    
    # Security risks
    security_patterns = [
        (r'password\s*=\s*["\']', "Possible hardcoded password"),
        (r'api[_-]?key\s*=\s*["\']', "Possible hardcoded API key"),
        (r'secret\s*=\s*["\']', "Possible hardcoded secret"),
        (r'eval\s*\(', "Use of eval() can be dangerous"),
        (r'exec\s*\(', "Use of exec() can be dangerous"),
        (r'subprocess\.call\(.*shell=True', "Shell injection risk"),
        (r'SELECT\s+.*\+', "Possible SQL injection"),
    ]
    
    for pattern, risk in security_patterns:
        if re.search(pattern, diff, re.IGNORECASE):
            risks.append(f"🔒 **Security**: {risk}")
    
    # Performance risks
    if 'TODO' in diff or 'FIXME' in diff:
        risks.append("⚠️ **Quality**: Contains TODO/FIXME comments")
    
    # Large changes
    if len(files) > 10:
        risks.append("📊 **Complexity**: Large PR with many file changes")
    
    # Breaking changes
    if re.search(r'BREAKING\s+CHANGE', diff, re.IGNORECASE):
        risks.append("💥 **Breaking**: PR contains breaking changes")
    
    # Test coverage
    test_files = [f for f in files if 'test' in f['path'].lower()]
    if not test_files and any(f['path'].endswith(('.py', '.js', '.ts')) for f in files):
        risks.append("🧪 **Testing**: No test files modified")
    
    return risks


def generate_suggestions(diff: str, files: List[Dict], risks: List[str]) -> List[str]:
    """Generate improvement suggestions."""
    suggestions = []
    
    # Based on risks
    if any('hardcoded' in risk.lower() for risk in risks):
        suggestions.append("🔐 Use environment variables for secrets instead of hardcoding")
    
    if any('TODO' in risk or 'FIXME' in risk for risk in risks):
        suggestions.append("📝 Resolve or document TODO/FIXME items before merging")
    
    if any('test' in risk.lower() for risk in risks):
        suggestions.append("✅ Add tests for new functionality")
    
    # General suggestions
    if len(files) > 10:
        suggestions.append("📦 Consider breaking into smaller PRs for easier review")
    
    # Code quality
    if re.search(r'print\s*\(', diff) and '.py' in str(files):
        suggestions.append("🎨 Replace print() with proper logging")
    
    if re.search(r'console\.log\(', diff) and '.js' in str(files):
        suggestions.append("🎨 Remove console.log() statements before merging")
    
    # Documentation
    readme_changed = any('README' in f['path'] for f in files)
    if not readme_changed and any(f['path'].endswith(('.py', '.js', '.ts')) for f in files):
        suggestions.append("📚 Update README if API or usage changes")
    
    return suggestions


def calculate_confidence(files: int, added: int, deleted: int, risk_count: int) -> str:
    """Calculate confidence score."""
    score = 100
    
    # Deduct for complexity
    if files > 10:
        score -= 20
    elif files > 5:
        score -= 10
    
    if added + deleted > 500:
        score -= 20
    elif added + deleted > 200:
        score -= 10
    
    # Deduct for risks
    score -= risk_count * 10
    
    # Determine confidence level
    if score >= 70:
        return "High"
    elif score >= 40:
        return "Medium"
    else:
        return "Low"


def format_markdown(review: ReviewResult, pr_url: str) -> str:
    """Format review as Markdown."""
    md = f"""# 🤖 Claude Code PR Review

> **Automated review by Claude Code Agent**
> **PR**: {pr_url}

---

## 📊 Summary

{review.summary}

---

## 📈 Statistics

- **Files Changed**: {review.files_changed}
- **Lines Added**: +{review.lines_added}
- **Lines Deleted**: -{review.lines_deleted}
- **Confidence**: **{review.confidence}**

---

## ⚠️ Identified Risks

"""
    
    if review.risks:
        for risk in review.risks:
            md += f"- {risk}\n"
    else:
        md += "✅ No significant risks identified\n"
    
    md += "\n---\n\n## 💡 Improvement Suggestions\n\n"
    
    if review.suggestions:
        for suggestion in review.suggestions:
            md += f"- {suggestion}\n"
    else:
        md += "✅ No specific suggestions at this time\n"
    
    md += f"""
---

## 📁 Files Modified

"""
    
    for file in review.files[:10]:  # Limit to first 10 files
        md += f"- `{file['path']}` (+{file['additions']} -{file['deletions']})\n"
    
    if len(review.files) > 10:
        md += f"\n_... and {len(review.files) - 10} more files_\n"
    
    md += """
---

**Generated by Claude Code PR Review Agent v1.0.0**
"""
    
    return md


def main():
    parser = argparse.ArgumentParser(
        description='Claude Code PR Review Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --pr https://github.com/owner/repo/pull/123
  %(prog)s --pr owner/repo#123
  %(prog)s --diff diff.txt
        """
    )
    
    parser.add_argument('--pr', help='GitHub PR URL or owner/repo#number')
    parser.add_argument('--diff', help='Path to diff file')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                       help='Output format (default: markdown)')
    
    args = parser.parse_args()
    
    if not args.pr and not args.diff:
        parser.error('Either --pr or --diff is required')
    
    # Get diff
    if args.pr:
        owner, repo, pr_number = parse_pr_url(args.pr)
        pr_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}"
        print(f"🔍 Fetching PR: {pr_url}", file=sys.stderr)
        diff = get_pr_diff(owner, repo, pr_number)
        pr_info = get_pr_info(owner, repo, pr_number)
    else:
        with open(args.diff, 'r') as f:
            diff = f.read()
        pr_url = "local diff file"
        pr_info = {'changedFiles': 0, 'additions': 0, 'deletions': 0, 'files': []}
    
    # Analyze
    print("🤖 Analyzing PR...", file=sys.stderr)
    review = analyze_diff(diff, pr_info)
    
    # Format output
    if args.format == 'markdown':
        output = format_markdown(review, pr_url)
    else:
        output = json.dumps(asdict(review), indent=2)
    
    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"✅ Review written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
