#!/usr/bin/env python3
"""
CHANGELOG Generator - Automatically generates structured CHANGELOG.md from git history.

Parses conventional commits and categorizes them into sections:
- Added (feat, feature)
- Fixed (fix, bugfix)
- Changed (refactor, perf, style, change)
- Removed (remove, delete)
- Deprecated (deprecate)
- Security (security)
- Documentation (docs, doc)
- Other (chore, test, build, ci)

Usage:
    python3 changelog-generator.py [--output CHANGELOG.md] [--tag v1.0.0]
    python3 changelog-generator.py --help

Author: Geldbert (AI Agent)
Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
"""

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Commit:
    """Represents a parsed conventional commit."""
    hash: str
    type: str
    scope: Optional[str]
    subject: str
    body: Optional[str]
    author: str
    date: str
    breaking: bool = False


# Conventional commit type to category mapping
TYPE_TO_CATEGORY = {
    'feat': 'Added',
    'feature': 'Added',
    'fix': 'Fixed',
    'bugfix': 'Fixed',
    'refactor': 'Changed',
    'perf': 'Changed',
    'performance': 'Changed',
    'style': 'Changed',
    'change': 'Changed',
    'remove': 'Removed',
    'delete': 'Removed',
    'deprecate': 'Deprecated',
    'security': 'Security',
    'docs': 'Documentation',
    'doc': 'Documentation',
    'chore': 'Other',
    'test': 'Other',
    'tests': 'Other',
    'build': 'Other',
    'ci': 'Other',
    'revert': 'Other',
}

# Category display order in CHANGELOG
CATEGORY_ORDER = [
    'Added',
    'Changed',
    'Deprecated',
    'Removed',
    'Fixed',
    'Security',
    'Documentation',
    'Other',
]


def run_git_command(args: list[str]) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ['git'] + args,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {' '.join(args)}", file=sys.stderr)
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def get_latest_tag() -> Optional[str]:
    """Get the latest git tag, or None if no tags exist."""
    try:
        return run_git_command(['describe', '--tags', '--abbrev=0'])
    except SystemExit:
        return None


def get_all_tags() -> list[str]:
    """Get all git tags in reverse chronological order."""
    try:
        tags = run_git_command(['tag', '--sort=-creatordate'])
        return tags.split('\n') if tags else []
    except SystemExit:
        return []


def get_commits_since_tag(tag: Optional[str] = None) -> list[dict]:
    """Get all commits since a tag (or all commits if no tag)."""
    if tag:
        log_format = '%H%n%s%n%b%n%an%n%aI%n---COMMIT_END---'
        log_range = f'{tag}..HEAD'
    else:
        log_format = '%H%n%s%n%b%n%an%n%aI%n---COMMIT_END---'
        log_range = 'HEAD'
    
    log_output = run_git_command([
        'log', log_range,
        '--format=' + log_format,
        '--no-merges',
    ])
    
    commits = []
    for commit_block in log_output.split('---COMMIT_END---'):
        commit_block = commit_block.strip()
        if not commit_block:
            continue
        
        lines = commit_block.split('\n', 4)
        if len(lines) < 5:
            lines.extend([''] * (5 - len(lines)))
        
        commits.append({
            'hash': lines[0][:7],  # Short hash
            'subject': lines[1],
            'body': lines[2] if len(lines) > 2 else '',
            'author': lines[3] if len(lines) > 3 else 'Unknown',
            'date': lines[4] if len(lines) > 4 else '',
        })
    
    return commits


def parse_conventional_commit(commit_data: dict) -> Optional[Commit]:
    """
    Parse a commit message following Conventional Commits spec.
    
    Format: type(scope)!: subject
    Examples:
        feat: add user login
        feat(auth): add OAuth support
        fix(api)!: breaking fix for API
        docs: update README
    """
    subject = commit_data['subject']
    
    # Regex for conventional commit format
    # type(scope)!: subject
    pattern = r'^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$'
    match = re.match(pattern, subject)
    
    if not match:
        return None
    
    commit_type = match.group(1).lower()
    scope = match.group(2)
    breaking = match.group(3) == '!'
    commit_subject = match.group(4)
    
    # Check body for BREAKING CHANGE
    body = commit_data.get('body', '')
    if body and 'BREAKING CHANGE' in body:
        breaking = True
    
    return Commit(
        hash=commit_data['hash'],
        type=commit_type,
        scope=scope,
        subject=commit_subject,
        body=body,
        author=commit_data['author'],
        date=commit_data['date'],
        breaking=breaking,
    )


def categorize_commits(commits: list[dict]) -> dict[str, list[Commit]]:
    """Parse and categorize commits by conventional commit type."""
    categories = defaultdict(list)
    
    for commit_data in commits:
        parsed = parse_conventional_commit(commit_data)
        if parsed:
            category = TYPE_TO_CATEGORY.get(parsed.type, 'Other')
            categories[category].append(parsed)
    
    return categories


def format_scope(scope: Optional[str]) -> str:
    """Format scope for display."""
    return f'**{scope}**: ' if scope else ''


def generate_changelog_section(commits: list[Commit], category: str) -> str:
    """Generate markdown section for a category."""
    if not commits:
        return ''
    
    lines = [f'### {category}', '']
    
    for commit in commits:
        scope_str = format_scope(commit.scope)
        breaking_str = ' **[BREAKING]**' if commit.breaking else ''
        lines.append(f'- {scope_str}{commit.subject}{breaking_str} ([{commit.hash}](../../commit/{commit.hash}))')
    
    lines.append('')
    return '\n'.join(lines)


def generate_changelog(
    categories: dict[str, list[Commit]],
    version: str,
    previous_tag: Optional[str] = None,
) -> str:
    """Generate the full CHANGELOG content."""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Header
    lines = [
        f'## [{version}] - {today}',
        '',
    ]
    
    if previous_tag:
        lines.append(f'[Compare with previous release]({previous_tag}...{version})')
        lines.append('')
    
    # Sections in order
    for category in CATEGORY_ORDER:
        if category in categories and categories[category]:
            lines.append(generate_changelog_section(categories[category], category))
    
    return '\n'.join(lines)


def get_repo_url() -> str:
    """Get the repository URL from git remote."""
    try:
        remote_url = run_git_command(['remote', 'get-url', 'origin'])
        # Convert SSH URL to HTTPS
        if remote_url.startswith('git@'):
            remote_url = remote_url.replace(':', '/').replace('git@', 'https://')
        # Remove .git suffix
        if remote_url.endswith('.git'):
            remote_url = remote_url[:-4]
        return remote_url
    except SystemExit:
        return ''


def generate_full_changelog(new_entry: str, existing_path: Path, repo_url: str) -> str:
    """Generate full CHANGELOG.md with new entry prepended."""
    header = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""
    
    content = header + new_entry
    
    # Append existing content (skip header)
    if existing_path.exists():
        existing = existing_path.read_text()
        # Remove existing header if present
        lines = existing.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('## '):
                start_idx = i
                break
        if start_idx > 0:
            content += '\n'.join(lines[start_idx:])
        elif existing.strip():
            content += existing
    
    return content


def main():
    parser = argparse.ArgumentParser(
        description='Generate CHANGELOG.md from git history using conventional commits.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Generate changelog for unreleased commits
  %(prog)s --tag v1.0.0             Tag version v1.0.0
  %(prog)s --output docs/CHANGELOG  Output to custom file
  %(prog)s --all                    Generate changelog for all commits

Conventional Commit Types:
  feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

Categories:
  Added       -> feat, feature
  Fixed       -> fix, bugfix
  Changed     -> refactor, perf, style, change
  Removed     -> remove, delete
  Deprecated  -> deprecate
  Security    -> security
  Documentation -> docs, doc
  Other       -> chore, test, build, ci
"""
    )
    
    parser.add_argument(
        '--output', '-o',
        default='CHANGELOG.md',
        help='Output file path (default: CHANGELOG.md)'
    )
    parser.add_argument(
        '--tag', '-t',
        help='Version tag for this release (e.g., v1.0.0)'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Include all commits, not just since last tag'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Print output without writing file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose output'
    )
    
    args = parser.parse_args()
    
    # Get previous tag
    previous_tag = get_latest_tag() if not args.all else None
    
    if args.verbose:
        if previous_tag:
            print(f"Previous tag: {previous_tag}", file=sys.stderr)
        else:
            print("No previous tags found. Processing all commits.", file=sys.stderr)
    
    # Get commits since last tag (or all)
    commits = get_commits_since_tag(None if args.all else previous_tag)
    
    if args.verbose:
        print(f"Found {len(commits)} commits", file=sys.stderr)
    
    if not commits:
        print("No commits to process.", file=sys.stderr)
        return
    
    # Parse and categorize
    categories = categorize_commits(commits)
    
    # Determine version
    version = args.tag if args.tag else 'Unreleased'
    
    # Generate changelog entry
    repo_url = get_repo_url()
    changelog_entry = generate_changelog(categories, version, previous_tag)
    
    # Build full changelog
    output_path = Path(args.output)
    full_changelog = generate_full_changelog(changelog_entry, output_path, repo_url)
    
    if args.dry_run:
        print(full_changelog)
    else:
        output_path.write_text(full_changelog)
        print(f"Generated {output_path}", file=sys.stderr)
        
        # Summary
        total = sum(len(c) for c in categories.values())
        print(f"  {total} commits processed", file=sys.stderr)
        for cat in CATEGORY_ORDER:
            if cat in categories and categories[cat]:
                print(f"  {cat}: {len(categories[cat])}", file=sys.stderr)


if __name__ == '__main__':
    main()