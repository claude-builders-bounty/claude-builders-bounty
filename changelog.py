#!/usr/bin/env python3
"""changelog.py - Generate a structured CHANGELOG.md from git history.

Usage:
    python changelog.py [--output CHANGELOG.md] [--repo /path/to/repo]
"""

import subprocess, os, sys, re, argparse
from collections import OrderedDict
from datetime import datetime

CATEGORIES = OrderedDict([
    ('Added',     ['feat', 'feature', 'add']),
    ('Fixed',     ['fix', 'bug', 'hotfix', 'bugfix']),
    ('Changed',   ['refactor', 'perf', 'chore', 'style', 'docs', 'test',
                   'update', 'improve', 'upgrade', 'migrate']),
    ('Removed',   ['remove', 'revert', 'delete', 'deprecate']),
])

def run_git(cmd, cwd=None, check=True):
    full_cmd = ['git'] + cmd
    r = subprocess.run(full_cmd, capture_output=True, text=True, cwd=cwd)
    if check and r.returncode != 0:
        return ''
    return r.stdout.strip()

def get_ref(cwd=None):
    """Get the ref to diff against: last tag, or first commit, or empty."""
    tag = run_git(['describe', '--tags', '--abbrev=0'], cwd, check=False)
    if tag:
        return tag
    first = run_git(['rev-list', '--max-parents=0', 'HEAD'], cwd, check=False)
    if first:
        return first
    return ''

COMMIT_TYPES = [
    'feat', 'feature', 'fix', 'bug', 'hotfix', 'bugfix',
    'refactor', 'perf', 'chore', 'style', 'docs', 'test',
    'remove', 'revert', 'delete', 'deprecate', 'update', 'improve',
    'upgrade', 'migrate', 'add'
]
TYPE_PATTERN = r'^(' + '|'.join(COMMIT_TYPES) + r')(?:\(([^)]*)\))?:\s*(.*)'

def parse_commit(subject):
    m = re.match(TYPE_PATTERN, subject, re.IGNORECASE)
    if m:
        return m.group(1).lower(), m.group(3)
    return 'other', subject

def categorize(subject):
    ct, desc = parse_commit(subject)
    for cat, kws in CATEGORIES.items():
        if ct in kws:
            return cat, desc
    if 'BREAKING CHANGE' in subject.upper() or (
        ':' in subject and '!' in subject.split(':')[0]):
        return 'Changed', subject
    return 'Changed', subject

SKIP = [
    r'^Merge branch', r'^Merge pull request',
    r'^chore\(release\)', r'^chore\(deps\)', r'^chore\(dep\)',
    r'^bump version', r'^v?\d+\.\d+\.\d+', r'^\d+\.\d+\.\d+',
]

def skip(subject):
    return any(re.match(p, subject) for p in SKIP)

def get_commits(since_ref, cwd=None):
    fmt = '%H||%s||%an||%ai'
    raw = run_git(['log', f'{since_ref}..HEAD', f'--format={fmt}'], cwd)
    if not raw:
        return []
    commits = []
    for line in raw.split('\n'):
        if not line.strip():
            continue
        parts = line.split('||', 3)
        if len(parts) == 4:
            commits.append({
                'hash': parts[0][:7],
                'subject': parts[1],
                'author': parts[2],
                'date': parts[3][:10],
            })
    return commits

def get_all_commits(cwd=None):
    fmt = '%H||%s||%an||%ai'
    raw = run_git(['log', '--all', f'--format={fmt}'], cwd)
    if not raw:
        return []
    commits = []
    for line in raw.split('\n'):
        if not line.strip():
            continue
        parts = line.split('||', 3)
        if len(parts) == 4:
            commits.append({
                'hash': parts[0][:7],
                'subject': parts[1],
                'author': parts[2],
                'date': parts[3][:10],
            })
    return commits

def generate(commits):
    sections = OrderedDict()
    for cat in CATEGORIES:
        sections[cat] = []

    for c in commits:
        if skip(c['subject']):
            continue
        category, desc = categorize(c['subject'])
        if category not in sections:
            sections[category] = []
        sections[category].append({
            'desc': desc[:100], 'hash': c['hash'],
            'author': c['author'],
        })

    lines = ['# Changelog', '',
        f'> Generated on {datetime.now().strftime("%Y-%m-%d")}', '']
    total = sum(len(v) for v in sections.values())
    if total == 0:
        lines.append('*No notable changes in this range.*')
        lines.append('')
        return '\n'.join(lines)

    for category, items in sections.items():
        if not items:
            continue
        lines.append(f'## {category}')
        lines.append('')
        for item in items:
            lines.append(f'- **{item["desc"]}** ({item["hash"]}) - {item["author"]}')
        lines.append('')

    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Generate CHANGELOG.md from git history')
    parser.add_argument('--output', '-o', default='CHANGELOG.md')
    parser.add_argument('--repo', '-r', default=None)
    args = parser.parse_args()

    cwd = args.repo or os.getcwd()
    if not os.path.isdir(os.path.join(cwd, '.git')):
        print(f'Error: {cwd} is not a git repo', file=sys.stderr)
        sys.exit(1)

    ref = get_ref(cwd)
    if ref:
        print(f'Generating changelog since: {ref[:12]}')
        commits = get_commits(ref, cwd)
    else:
        print('No tags or commits found. Using all commits.')
        commits = get_all_commits(cwd)

    if not commits:
        print('No commits found.')
        return

    changelog = generate(commits)
    out = args.output if os.path.isabs(args.output) else os.path.join(cwd, args.output)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(changelog)

    print(f'Changelog written to {out}')
    print(f'  {len(commits)} commits processed')
    included = sum(1 for c in commits if not skip(c['subject']))
    print(f'  {included} changes included')

if __name__ == '__main__':
    main()
