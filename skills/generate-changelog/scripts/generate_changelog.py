#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history."""

import subprocess, re, sys, os
from datetime import date

def get_last_tag():
    """Get the last git tag."""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # No tags yet, get all commits
        return None

def get_commits_since_tag(tag):
    """Get commits since the last tag."""
    if tag:
        cmd = ['git', 'log', f'{tag}..HEAD', '--format=%h %s']
    else:
        cmd = ['git', 'log', '--format=%h %s']
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip().split('\n') if result.stdout.strip() else []

def categorize_commit(commit_msg):
    """Categorize a commit based on its message."""
    msg_lower = commit_msg.lower()
    if re.match(r'feat(\(.*\))?!?:', msg_lower) or re.match(r'add(s)?[\s:]+', msg_lower):
        return 'Added'
    elif re.match(r'fix(\(.*\))?!?:', msg_lower) or re.match(r'bugfix[\s:]+', msg_lower):
        return 'Fixed'
    elif re.match(r'remove(s)?[\s:]+', msg_lower) or re.match(r'delete(s)?[\s:]+', msg_lower):
        return 'Removed'
    else:
        return 'Changed'

def generate_changelog(commits):
    """Generate CHANGELOG.md content."""
    today = date.today().isoformat()
    lines = [
        '# Changelog',
        '',
        '## [Unreleased] - ' + today,
        ''
    ]
    
    categories = {'Added': [], 'Fixed': [], 'Changed': [], 'Removed': []}
    for commit in commits:
        if not commit.strip():
            continue
        parts = commit.split(' ', 1)
        if len(parts) < 2:
            continue
        sha, msg = parts[0], parts[1]
        category = categorize_commit(msg)
        categories[category].append((sha, msg))
    
    for cat in ['Added', 'Fixed', 'Changed', 'Removed']:
        if categories[cat]:
            lines.append('### ' + cat)
            for sha, msg in categories[cat]:
                lines.append('- ' + msg + ' (' + sha + ')')
            lines.append('')
    
    return '\n'.join(lines)

def main():
    last_tag = get_last_tag()
    if last_tag:
        print('Last tag: ' + last_tag)
        commits = get_commits_since_tag(last_tag)
    else:
        print('No tags found, using all commits')
        commits = get_commits_since_tag(None)
    
    if not commits:
        print('No commits found since last tag.')
        sys.exit(0)
    
    print('Found ' + str(len(commits)) + ' commits.')
    changelog = generate_changelog(commits)
    
    with open('CHANGELOG.md', 'w') as f:
        f.write(changelog)
    print('CHANGELOG.md generated successfully!')

if __name__ == '__main__':
    main()
