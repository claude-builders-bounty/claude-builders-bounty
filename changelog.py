#!/usr/bin/env python3
"""Generate a Keep-a-Changelog-style Markdown file from commits after the latest reachable tag."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess

SECTIONS = ('Added', 'Fixed', 'Changed', 'Removed')

def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True).stdout

def classify(subject):
    match = re.match(r'^([\w-]+)(?:\([^)]+\))?(!)?:\s*(.*)$', subject, re.I)
    if match:
        kind, breaking, message = match.groups()
        kind = kind.lower()
        if kind in ('feat', 'feature', 'add'): return 'Added', message
        if kind in ('fix', 'bugfix', 'hotfix'): return 'Fixed', message
        if kind in ('remove', 'delete', 'revert'): return 'Removed', message
        if breaking: return 'Changed', message
        return 'Changed', message
    if re.search(r'\b(remov(?:e|ed|ing)|delet(?:e|ed|ing)|deprecat(?:e|ed|ing))\b', subject, re.I): return 'Removed', subject
    if re.search(r'\b(fix(?:ed|es)?|bug|repair(?:ed)?|patch(?:ed)?)\b', subject, re.I): return 'Fixed', subject
    if re.search(r'\b(add(?:ed|s)?|introduc(?:e|ed)|new)\b', subject, re.I): return 'Added', subject
    return 'Changed', subject

def generate():
    try:
        git('rev-parse', '--is-inside-work-tree')
        tag = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], capture_output=True, text=True)
        latest = tag.stdout.strip() if tag.returncode == 0 else None
        log_range = f'{latest}..HEAD' if latest else 'HEAD'
        data = git('log', log_range, '--format=%s%x00')
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise ValueError('Run this script inside a Git repository with at least one commit.') from exc
    sections = {section: [] for section in SECTIONS}
    for raw in data.split(b'\0'):
        subject = raw.decode('utf-8', errors='replace').strip()
        if not subject: continue
        section, message = classify(subject)
        sections[section].append(message.strip())
    date = datetime.now(timezone.utc).date().isoformat()
    lines = ['# Changelog', '', 'All notable changes since the latest reachable Git tag.', '', f'## [Unreleased] - {date}', '']
    if latest:
        lines.extend([f'_Changes since tag `{latest}`._', ''])
    if not any(sections.values()):
        lines.extend(['No changes since the latest tag.', ''])
    else:
        for section, messages in sections.items():
            if messages:
                lines.extend([f'### {section}', ''])
                lines.extend(f'- {msg}' for msg in messages)
                lines.append('')
    return '\n'.join(lines) + '\n'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='CHANGELOG.md', help='Output file path')
    parser.add_argument('--force', action='store_true', help='Overwrite an existing file')
    args = parser.parse_args()
    path = Path(args.output)
    if path.exists() and not args.force:
        parser.error(f'{path} already exists; use --force to overwrite')
    try:
        content = generate()
    except ValueError as exc:
        parser.error(str(exc))
    path.write_text(content, encoding='utf-8')
    print(f'Generated {path}')

if __name__ == '__main__':
    main()
