#!/usr/bin/env python3
"""
Changelog Generator — Auto-generate structured CHANGELOG.md from git history.

Usage:
  python3 changelog.sh              # Generates CHANGELOG.md in current dir
  python3 changelog.sh --from v1.0  # Start from a specific tag
  python3 changelog.sh --output HISTORY.md  # Custom output file
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ── Commit Categorization ──────────────────────────────────────────────────

# Pattern -> category mapping (order matters: first match wins)
COMMIT_PATTERNS = [
    # Added
    (r'^(feat|feature|add|implement|create|new)', 'Added'),
    (r'^(✨|🌟|🚀|🎉)', 'Added'),
    # Fixed
    (r'^(fix|bugfix|bug|hotfix|patch|correct|resolve)', 'Fixed'),
    (r'^(🐛|🔧|🩹)', 'Fixed'),
    # Changed
    (r'^(refactor|update|upgrade|migrate|redesign|revamp|improve|optimize|perf)', 'Changed'),
    (r'^(♻️|⚡|🔄|📦)', 'Changed'),
    # Removed
    (r'^(remove|delete|deprecate|drop|cleanup|chore.*clean)', 'Removed'),
    (r'^(🗑️|🔥|🧹)', 'Removed'),
    # Documentation
    (r'^(docs|doc|document|readme)', 'Documentation'),
    (r'^(📝|📖|📚)', 'Documentation'),
    # Testing
    (r'^(test|tests|testing)', 'Testing'),
    (r'^(✅|🧪)', 'Testing'),
    # CI/CD
    (r'^(ci|cd|devops|build|docker)', 'CI/CD'),
    (r'^(👷|🔨|🐳)', 'CI/CD'),
]


def categorize_commit(message):
    """Categorize a commit message into Added/Fixed/Changed/Removed/etc."""
    first_line = message.split('\n')[0].strip().lower()
    for pattern, category in COMMIT_PATTERNS:
        if re.match(pattern, first_line):
            return category
    return 'Changed'  # Default


# ── Git Operations ─────────────────────────────────────────────────────────

def get_last_tag():
    """Get the most recent git tag sorted by version."""
    try:
        result = subprocess.run(
            ['git', 'tag', '--sort=-v:refname'],
            capture_output=True, text=True, timeout=10
        )
        tags = [t.strip() for t in result.stdout.split('\n') if t.strip()]
        if tags:
            return tags[0]
    except Exception:
        pass
    return None


def get_commits_since(tag=None):
    """Get commits since a given tag (or all commits if no tag)."""
    if tag:
        args = ['git', 'log', f'{tag}..HEAD', '--oneline', '--format=%H|%ct|%an|%s']
    else:
        # Try to get the first commit as starting point
        try:
            first = subprocess.run(
                ['git', 'rev-list', '--max-parents=0', 'HEAD'],
                capture_output=True, text=True, timeout=10
            )
            first_sha = first.stdout.strip()
            args = ['git', 'log', '--oneline', '--format=%H|%ct|%an|%s']
        except Exception:
            args = ['git', 'log', '--oneline', '--format=%H|%ct|%an|%s']

    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    commits = []
    for line in result.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.strip().split('|', 3)
        if len(parts) == 4:
            sha, ts, author, message = parts
            commits.append({
                'sha': sha,
                'timestamp': datetime.fromtimestamp(int(ts)),
                'author': author,
                'message': message,
                'category': categorize_commit(message),
            })
    return commits


# ── Changelog Generation ────────────────────────────────────────────────────

CATEGORY_ORDER = ['Added', 'Fixed', 'Changed', 'Removed', 'Documentation', 'Testing', 'CI/CD']
CATEGORY_EMOJIS = {
    'Added': '🚀',
    'Fixed': '🐛',
    'Changed': '🔄',
    'Removed': '🗑️',
    'Documentation': '📝',
    'Testing': '🧪',
    'CI/CD': '👷',
}


def generate_changelog(commits, version=None, since_tag=None):
    """Generate a formatted CHANGELOG.md string."""
    lines = []
    today = datetime.now().strftime('%Y-%m-%d')
    ver = version or 'Unreleased'
    tag_info = f' (since {since_tag})' if since_tag else ''

    lines.append(f'# Changelog{tag_info}')
    lines.append('')
    lines.append(f'## [{ver}] — {today}')
    lines.append('')

    # Group by category
    grouped = {cat: [] for cat in CATEGORY_ORDER}
    for c in commits:
        cat = c['category'] if c['category'] in grouped else 'Changed'
        grouped[cat].append(c)

    for cat in CATEGORY_ORDER:
        cat_commits = grouped[cat]
        if not cat_commits:
            continue
        emoji = CATEGORY_EMOJIS.get(cat, '🔹')
        lines.append(f'### {emoji} {cat}')
        lines.append('')
        for c in cat_commits:
            short_sha = c['sha'][:7]
            lines.append(f'- {c["message"]} ([{short_sha}](https://github.com/{get_repo_name()}/commit/{c["sha"]}))')
        lines.append('')

    if not commits:
        lines.append('No changes yet.')
        lines.append('')

    return '\n'.join(lines)


def get_repo_name():
    """Get the GitHub repo name from git remote."""
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True, text=True, timeout=5
        )
        url = result.stdout.strip()
        # Parse: git@github.com:user/repo.git or https://github.com/user/repo
        m = re.search(r'(?:github\.com[:/])([\w-]+/[\w-]+?)(?:\.git)?$', url)
        if m:
            return m.group(1)
    except Exception:
        pass
    return 'user/repo'


# ── CLI Entry Point ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Generate CHANGELOG.md from git history')
    parser.add_argument('--from', dest='from_tag', help='Tag to start from (default: auto-detect)')
    parser.add_argument('--output', '-o', default='CHANGELOG.md', help='Output file (default: CHANGELOG.md)')
    parser.add_argument('--stdout', action='store_true', help='Print to stdout instead of file')
    args = parser.parse_args()

    # Determine starting point
    since_tag = args.from_tag or get_last_tag()
    if since_tag:
        print(f'📋 Generating changelog since {since_tag}...')
    else:
        print('📋 Generating changelog from all commits...')

    # Get commits
    commits = get_commits_since(since_tag)
    if not commits:
        print('❌ No commits found.')
        sys.exit(1)

    print(f'📝 Found {len(commits)} commit(s)')

    # Generate
    version = since_tag or '0.1.0'
    changelog = generate_changelog(commits, version=version, since_tag=since_tag)

    if args.stdout:
        print('\n' + changelog)
    else:
        with open(args.output, 'w') as f:
            f.write(changelog + '\n')
        print(f'✅ Generated {args.output}')

    # Show summary
    categories = {}
    for c in commits:
        cat = c['category']
        categories[cat] = categories.get(cat, 0) + 1
    print('📊 Summary: ' + ', '.join(f'{cat}: {count}' for cat, count in categories.items()))


if __name__ == '__main__':
    main()
