#!/usr/bin/env python3
"""Generate the Unreleased changelog from commits after the nearest reachable tag."""
import argparse
import re
import subprocess
from pathlib import Path

CATEGORIES = ('Added', 'Fixed', 'Changed', 'Removed')

def git(repo, *args, optional=False):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, encoding='utf-8')
    if result.returncode and not optional:
        raise RuntimeError(result.stderr.strip() or 'Git command failed')
    return result.stdout.strip() if result.returncode == 0 else None

def read_commits(repo, run=git):
    run(repo, 'rev-parse', '--verify', 'HEAD')
    if run(repo, 'rev-parse', '--is-shallow-repository') == 'true':
        raise RuntimeError('Shallow history cannot establish the release boundary; fetch complete history first.')
    tag = run(repo, 'describe', '--tags', '--abbrev=0', optional=True)
    revision = f'{tag}..HEAD' if tag else 'HEAD'
    raw = run(repo, 'log', '--no-merges', '--format=%H%x09%s', revision, '--')
    return tag, parse_commits(raw)

def parse_commits(raw):
    commits = []
    for line in raw.splitlines():
        sha, separator, subject = line.partition('\t')
        if not separator or not re.fullmatch(r'[0-9a-fA-F]{40,64}', sha):
            raise ValueError('Invalid git log record')
        commits.append((sha, subject))
    return commits

def category(subject):
    match = re.match(r'(?i)^(\w+)(?:\([^)]*\))?!?:\s*(.*)', subject)
    kind = match.group(1).lower() if match else ''
    text = match.group(2) if match else subject
    if kind in ('remove', 'delete') or re.match(r'(?i)^(remove|delete|drop)\b', text):
        return 'Removed'
    if kind == 'feat':
        return 'Added'
    if kind == 'fix':
        return 'Fixed'
    return 'Changed'

def render(commits):
    grouped = {name: [] for name in CATEGORIES}
    for sha, subject in commits:
        # Subjects are plain text, not trusted Markdown or HTML.
        safe = subject.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        safe = re.sub(r'([\\`*_\[\]])', r'\\\1', safe)
        grouped[category(subject)].append(f'- {safe} ({sha[:7]})')
    sections = ['## Unreleased']
    for name, rows in grouped.items():
        if rows:
            sections.append('### ' + name + '\n' + '\n'.join(rows))
    return '\n\n'.join(sections) + '\n'

def update_changelog(existing, commits):
    if not commits:
        return existing  # Never erase pending notes when there are no new commits.
    section = render(commits)
    starts = list(re.finditer(r'(?m)^## (?:\[)?Unreleased(?:\])?[^\r\n]*\r?$', existing, re.IGNORECASE))
    if len(starts) > 1:
        raise ValueError('Multiple Unreleased sections; refusing ambiguous replacement')
    if starts:
        start = starts[0].start()
        next_heading = re.search(r'(?m)^## ', existing[starts[0].end():])
        end = starts[0].end() + next_heading.start() if next_heading else len(existing)
        return existing[:start] + section + ('\n' if end < len(existing) else '') + existing[end:]
    first_release = re.search(r'(?m)^## ', existing)
    if first_release:
        return existing[:first_release.start()] + section + '\n' + existing[first_release.start():]
    return (existing.rstrip() + '\n\n' if existing.strip() else '# Changelog\n\n') + section

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, help='Defaults to CHANGELOG.md at repository root')
    parser.add_argument('--stdout', action='store_true', help='Preview without writing')
    args = parser.parse_args(argv)
    root = Path(git(args.repo, 'rev-parse', '--show-toplevel'))
    tag, commits = read_commits(root)
    target = args.output or root / 'CHANGELOG.md'
    if target.is_symlink():
        raise ValueError('Refusing to replace a symlink')
    existing = target.read_text(encoding='utf-8') if target.exists() else ''
    result = update_changelog(existing, commits)
    if args.stdout:
        print(result, end='')
    elif commits:
        target.write_text(result, encoding='utf-8', newline='\n')
        print(f'Updated {target}: {len(commits)} commits since {tag or "initial history"}')
    else:
        print('No commits since the latest tag; file unchanged.')

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        raise SystemExit(str(error))
