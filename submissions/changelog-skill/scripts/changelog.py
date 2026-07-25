#!/usr/bin/env python3
"""Generate structured CHANGELOG.md from git history."""
import subprocess, sys, re, argparse, os
from datetime import date

CATEGORIES = {
    'Added': [],
    'Fixed': [],
    'Changed': [],
    'Removed': [],
    'Security': [],
}

PREFIX_MAP = {
    'feat': 'Added',
    'fix': 'Fixed',
    'refactor': 'Changed',
    'perf': 'Changed',
    'style': 'Changed',
    'revert': 'Removed',
    'remove': 'Removed',
    'security': 'Security',
    'sec': 'Security',
}

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def get_commits(since_tag):
    if since_tag:
        log = run(f'git log {since_tag}..HEAD --pretty=format:%h##%s')
    else:
        log = run('git log --pretty=format:%h##%s')
    return [l.split('##', 1) for l in log.split('\n') if l] if log else []

def categorize(sha, msg):
    msg_lower = msg.lower()
    for prefix, cat in PREFIX_MAP.items():
        if msg_lower.startswith(f'{prefix}:') or msg_lower.startswith(f'{prefix}('):
            return cat, f"{sha} {msg}"
    # Uncategorized → Changed
    return 'Changed', f"{sha} {msg}"

def generate(since_tag=None, output_path=None):
    commits = get_commits(since_tag)
    if not commits:
        print("No commits found.")
        return

    for sha, msg in commits:
        cat, entry = categorize(sha, msg)
        CATEGORIES[cat].append(f"- {entry}")

    tag = since_tag or 'Unreleased'
    today = date.today().isoformat()
    ver = tag.lstrip('v')
    
    lines = [
        f'# Changelog',
        f'',
        f'## [{ver}] - {today}' if tag != 'Unreleased' else f'## [Unreleased]',
        f'',
    ]
    
    for cat in ['Added', 'Fixed', 'Changed', 'Removed', 'Security']:
        if CATEGORIES[cat]:
            lines.append(f'### {cat}')
            lines.extend(CATEGORIES[cat])
            lines.append('')
    
    output = '\n'.join(lines)
    
    if output_path:
        existing = ''
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                existing = f.read()
        # Insert after first ## heading
        with open(output_path, 'w') as f:
            if '## [' in existing:
                parts = existing.split('\n## ', 1)
                f.write(parts[0] + '\n' + '\n## '.join([output.split('\n## ', 1)[1], parts[1]]))
            else:
                f.write(output)
        print(f'Wrote {output_path}')
    else:
        print(output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate CHANGELOG from git history')
    parser.add_argument('--since', default='', help='Git tag/ref to start from')
    parser.add_argument('--output', default='', help='Output file (prints to stdout if omitted)')
    args = parser.parse_args()
    
    since = args.since or run('git describe --tags --abbrev=0 2>/dev/null') or ''
    generate(since, args.output)
