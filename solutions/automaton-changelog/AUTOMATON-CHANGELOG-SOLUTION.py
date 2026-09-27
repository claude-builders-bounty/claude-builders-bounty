#!/usr/bin/env python3
"""Generate CHANGELOG.md from commits since the latest reachable Git tag."""
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

CATEGORIES = ('Added', 'Fixed', 'Changed', 'Removed')
PREFIXES = {
    'Added': re.compile(r'^(?:feat|feature|add)(?:\([^)]*\))?!?:\s*', re.I),
    'Fixed': re.compile(r'^(?:fix|bug)(?:\([^)]*\))?!?:\s*', re.I),
    'Changed': re.compile(r'^(?:change|refactor|perf)(?:\([^)]*\))?!?:\s*', re.I),
    'Removed': re.compile(r'^(?:remove|delete)(?:\([^)]*\))?!?:\s*', re.I),
}

def git(*args):
    return subprocess.run(['git', *args], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()

def generate():
    try:
        git('rev-parse', '--is-inside-work-tree')
        try:
            base = git('describe', '--tags', '--abbrev=0')
        except subprocess.CalledProcessError:
            base = None
        history = git('log', *( [f'{base}..HEAD'] if base else [] ), '--date=short', '--pretty=format:%h%x1f%s%x1f%ad%x1e')
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f'Cannot read Git history: {exc}', file=sys.stderr)
        return 2
    groups = defaultdict(list)
    count = 0
    for record in history.split('\x1e'):
        record = record.strip()
        if not record:
            continue
        parts = record.split('\x1f')
        if len(parts) != 3:
            print('Malformed Git log record', file=sys.stderr)
            return 2
        short_hash, subject, committed = parts
        count += 1
        category = 'Changed'
        for name, pattern in PREFIXES.items():
            match = pattern.match(subject)
            if match:
                category = name
                subject = subject[match.end():]
                break
        groups[category].append(f'- {subject} ({short_hash}, {committed})')
    lines = ['# Changelog', '', f'<!-- Generated {date.today().isoformat()} by Automaton; review before publishing. -->', '', f'## Changes since {base}' if base else '## Changes', '']
    if count == 0:
        lines.append('No commits found since the selected baseline.')
    else:
        for category in CATEGORIES:
            if groups[category]:
                lines.extend((f'### {category}', *groups[category], ''))
    Path('CHANGELOG.md').write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
    print(f'Wrote CHANGELOG.md from {count} commit(s). Review the result.')
    return 0

if __name__ == '__main__':
    raise SystemExit(generate())
