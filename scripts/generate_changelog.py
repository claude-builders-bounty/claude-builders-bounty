#!/usr/bin/env python3
"""
CHANGELOG Generator
Generates a structured CHANGELOG.md from git history since the last tag.
Auto-categorizes commits into: Added, Fixed, Changed, Removed.
"""

import subprocess
import re
import sys
import os
from datetime import datetime

CATEGORIES = {
    'Added': [r'^feat', r'^add', r'^new', r'^implement'],
    'Fixed': [r'^fix', r'^bug', r'^patch', r'^resolve', r'^repair'],
    'Changed': [r'^chore', r'^refactor', r'^update', r'^change', r'^tweak', r'^improve'],
    'Removed': [r'^remove', r'^delete', r'^drop', r'^deprecate', r'^clean'],
}


def run_git(cmd: list[str]) -> str:
    result = subprocess.run(['git'] + cmd, capture_output=True, text=True, cwd=os.getcwd())
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(cmd)} failed: {result.stderr}")
    return result.stdout.strip()


def get_last_tag() -> str | None:
    try:
        tag = run_git(['describe', '--tags', '--abbrev=0'])
        return tag
    except RuntimeError:
        return None


def get_commits_since_tag(tag: str | None) -> list[dict]:
    if tag:
        log = run_git(['log', f'{tag}..HEAD', '--pretty=format:%H|||%s|||%an|||%ai'])
    else:
        log = run_git(['log', '--pretty=format:%H|||%s|||%an|||%ai'])

    if not log:
        return []

    commits = []
    for line in log.split('\n'):
        parts = line.split('|||', 3)
        if len(parts) == 4:
            commits.append({
                'hash': parts[0][:7],
                'message': parts[1],
                'author': parts[2],
                'date': parts[3][:10],
            })
    return commits


def categorize(message: str) -> str:
    msg_lower = message.lower().strip()
    for category, patterns in CATEGORIES.items():
        for pattern in patterns:
            if re.match(pattern, msg_lower):
                return category
    return 'Changed'


def generate_changelog(commits: list[dict], repo_name: str) -> str:
    today = datetime.now().strftime('%Y-%m-%d')

    categorized = {'Added': [], 'Fixed': [], 'Changed': [], 'Removed': []}
    for c in commits:
        cat = categorize(c['message'])
        categorized[cat].append(c)

    lines = ['# Changelog', '', f'## [{today}]', '']

    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        entries = categorized[cat]
        if not entries:
            continue
        lines.append(f'### {cat}')
        for c in entries:
            msg = c['message']
            msg = re.sub(r'^(feat|fix|chore|refactor|docs|test|style|perf|ci|build)[(:]\s*', '', msg, flags=re.IGNORECASE)
            msg = msg[0].upper() + msg[1:]
            hash_short = c['hash']
            lines.append(f'- {msg} ({hash_short})')
        lines.append('')

    # Add stats
    total = len(commits)
    lines.append(f'> {total} commits since last tag.')

    return '\n'.join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate structured CHANGELOG.md from git history')
    parser.add_argument('--output', '-o', default='CHANGELOG.md', help='Output file (default: CHANGELOG.md)')
    parser.add_argument('--repo-name', '-r', default=None, help='Repository name (auto-detected if omitted)')
    parser.add_argument('--prepend', '-p', action='store_true', help='Prepend to existing CHANGELOG instead of overwriting')
    args = parser.parse_args()

    try:
        run_git(['rev-parse', '--is-inside-work-tree'])
    except RuntimeError:
        print('ERROR: Not inside a git repository.', file=sys.stderr)
        sys.exit(1)

    repo_name = args.repo_name or os.path.basename(os.getcwd())
    tag = get_last_tag()
    commits = get_commits_since_tag(tag)

    if not commits:
        print(f'No commits found since tag: {tag or "beginning"}')
        sys.exit(0)

    changelog = generate_changelog(commits, repo_name)

    if args.prepend and os.path.exists(args.output):
        with open(args.output, 'r') as f:
            existing = f.read()
        changelog = changelog + '\n\n' + existing

    with open(args.output, 'w') as f:
        f.write(changelog)

    print(f'✅ CHANGELOG.md generated with {len(commits)} commits')
    if tag:
        print(f'   Since tag: {tag}')
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        count = sum(1 for c in commits if categorize(c['message']) == cat)
        if count:
            print(f'   {cat}: {count}')
    print(f'   Output: {os.path.abspath(args.output)}')


if __name__ == '__main__':
    main()
