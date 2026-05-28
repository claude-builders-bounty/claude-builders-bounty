#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent

CLI tool that fetches a PR diff, analyzes it, and posts a structured Markdown review.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PRInfo:
    """PR metadata."""
    owner: str
    repo: str
    number: int
    title: str
    body: str
    diff: str
    files_changed: list[str]
    additions: int
    deletions: int


@dataclass
class Review:
    """Structured review output."""
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str  # Low, Medium, High
    raw_analysis: str


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into owner, repo, number."""
    pattern = r'github\.com/([^/]+)/([^/]+)/pull/(\d+)'
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_info(owner: str, repo: str, number: int, token: Optional[str] = None) -> PRInfo:
    """Fetch PR metadata and diff from GitHub API."""
    if not token:
        token = os.environ.get('GITHUB_TOKEN')
    
    headers = []
    if token:
        headers = ['-H', f'Authorization: token {token}']
    
    # Fetch PR metadata
    pr_cmd = ['curl', '-s'] + headers + [
        f'https://api.github.com/repos/{owner}/{repo}/pulls/{number}'
    ]
    pr_result = subprocess.run(pr_cmd, capture_output=True, text=True)
    pr_data = json.loads(pr_result.stdout)
    
    # Fetch PR diff
    diff_cmd = ['curl', '-s'] + headers + [
        '-H', 'Accept: application/vnd.github.v3.diff',
        f'https://api.github.com/repos/{owner}/{repo}/pulls/{number}'
    ]
    diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
    
    # Fetch files changed
    files_cmd = ['curl', '-s'] + headers + [
        f'https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files'
    ]
    files_result = subprocess.run(files_cmd, capture_output=True, text=True)
    files_data = json.loads(files_result.stdout)
    
    return PRInfo(
        owner=owner,
        repo=repo,
        number=number,
        title=pr_data.get('title', ''),
        body=pr_data.get('body', ''),
        diff=diff_result.stdout,
        files_changed=[f['filename'] for f in files_data],
        additions=pr_data.get('additions', 0),
        deletions=pr_data.get('deletions', 0)
    )


def analyze_diff(pr_info: PRInfo) -> Review:
    """Analyze PR diff and generate structured review."""
    diff = pr_info.diff
    title = pr_info.title
    body = pr_info.body
    
    # Extract key information from diff
    added_lines = []
    removed_lines = []
    file_types = set()
    
    for line in diff.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:])
        elif line.startswith('-') and not line.startswith('---'):
            removed_lines.append(line[1:])
    
    # Detect file types
    for f in pr_info.files_changed:
        if '.' in f:
            ext = f.rsplit('.', 1)[-1]
            file_types.add(ext)
    
    # Generate summary
    summary_parts = []
    summary_parts.append(f"PR modifies {len(pr_info.files_changed)} file(s)")
    summary_parts.append(f"with {pr_info.additions} additions and {pr_info.deletions} deletions.")
    
    if 'py' in file_types:
        summary_parts.append("Changes involve Python code.")
    if 'js' in file_types or 'ts' in file_types:
        summary_parts.append("Changes involve JavaScript/TypeScript.")
    if 'md' in file_types:
        summary_parts.append("Documentation changes included.")
    
    summary = ' '.join(summary_parts)
    
    # Identify risks
    risks = []
    
    # Check for potential issues
    diff_lower = diff.lower()
    
    if 'eval(' in diff or 'exec(' in diff:
        risks.append("⚠️ Use of eval()/exec() detected — potential code injection risk")
    
    if 'subprocess' in diff and 'shell=True' in diff:
        risks.append("⚠️ subprocess with shell=True — potential command injection")
    
    if 'password' in diff_lower or 'secret' in diff_lower or 'token' in diff_lower:
        risks.append("⚠️ Potential hardcoded credentials or secrets")
    
    if 'TODO' in diff or 'FIXME' in diff or 'HACK' in diff:
        risks.append("⚠️ TODO/FIXME/HACK comments found — unfinished work")
    
    if 'print(' in diff and 'logging' not in diff_lower:
        risks.append("⚠️ print() statements without logging framework")
    
    if pr_info.deletions > pr_info.additions * 2:
        risks.append("⚠️ Significant code removal — ensure tests still pass")
    
    if not risks:
        risks.append("✅ No obvious risks detected")
    
    # Generate suggestions
    suggestions = []
    
    if 'test' not in ' '.join(pr_info.files_changed).lower():
        suggestions.append("📝 Consider adding tests for the changes")
    
    if 'readme' not in ' '.join(pr_info.files_changed).lower() and len(pr_info.files_changed) > 2:
        suggestions.append("📝 Consider updating README if behavior changed")
    
    if any(f.endswith('.py') for f in pr_info.files_changed):
        if 'type' not in diff_lower and 'hint' not in diff_lower:
            suggestions.append("📝 Consider adding type hints to Python code")
    
    if any(f.endswith(('.js', '.ts')) for f in pr_info.files_changed):
        if 'interface' not in diff and 'type' not in diff:
            suggestions.append("📝 Consider adding TypeScript interfaces/types")
    
    if len(pr_info.files_changed) > 10:
        suggestions.append("📝 Large PR — consider splitting into smaller PRs")
    
    if not suggestions:
        suggestions.append("✅ No additional suggestions")
    
    # Determine confidence
    confidence = "Medium"
    
    if len(risks) == 1 and risks[0].startswith("✅"):
        confidence = "High"
    elif any("⚠️" in r for r in risks):
        confidence = "Low"
    
    # Raw analysis
    raw_analysis = f"""
## PR Analysis: {title}

**Files Changed:** {', '.join(pr_info.files_changed[:10])}
{'  ... and more' if len(pr_info.files_changed) > 10 else ''}

**File Types:** {', '.join(sorted(file_types))}

**Lines:** +{pr_info.additions} / -{pr_info.deletions}
"""
    
    return Review(
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
        raw_analysis=raw_analysis
    )


def format_review_markdown(review: Review, pr_info: PRInfo) -> str:
    """Format review as structured Markdown."""
    md = f"""## 🤖 PR Review

### Summary
{review.summary}

### Risks
{chr(10).join(f'- {r}' for r in review.risks)}

### Suggestions
{chr(10).join(f'- {s}' for s in review.suggestions)}

### Confidence: {review.confidence}

---

<details>
<summary>Detailed Analysis</summary>

{review.raw_analysis}

</details>
"""
    return md


def post_comment(owner: str, repo: str, number: int, body: str, token: Optional[str] = None):
    """Post a comment on a GitHub PR."""
    if not token:
        token = os.environ.get('GITHUB_TOKEN')
    
    if not token:
        print("Error: GITHUB_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    
    # Write body to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({'body': body}, f)
        tmp_path = f.name
    
    cmd = [
        'curl', '-s', '-X', 'POST',
        '-H', f'Authorization: token {token}',
        '-H', 'Content-Type: application/json',
        '-d', f'@{tmp_path}',
        f'https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(tmp_path)
    
    response = json.loads(result.stdout)
    if 'id' in response:
        print(f"✅ Comment posted: {response.get('html_url', 'N/A')}")
    else:
        print(f"❌ Error posting comment: {response}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Claude Code PR Reviewer Agent')
    parser.add_argument('--pr', required=True, help='GitHub PR URL')
    parser.add_argument('--post', action='store_true', help='Post review as comment')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--token', help='GitHub token (or set GITHUB_TOKEN env var)')
    
    args = parser.parse_args()
    
    # Parse PR URL
    owner, repo, number = parse_pr_url(args.pr)
    print(f"📋 Fetching PR #{number} from {owner}/{repo}...")
    
    # Fetch PR info
    pr_info = fetch_pr_info(owner, repo, number, args.token)
    print(f"📊 Analyzing {len(pr_info.files_changed)} files (+{pr_info.additions}/-{pr_info.deletions})...")
    
    # Generate review
    review = analyze_diff(pr_info)
    
    # Format as Markdown
    markdown = format_review_markdown(review, pr_info)
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(markdown)
        print(f"📝 Review saved to {args.output}")
    
    print("\n" + markdown)
    
    # Post comment if requested
    if args.post:
        post_comment(owner, repo, number, markdown, args.token)


if __name__ == '__main__':
    main()
