#!/usr/bin/env python3
"""Generate a deterministic changelog from reachable Git history (stdlib only)."""
import argparse
from pathlib import Path
import re
import subprocess
import sys

CATEGORIES = ('Added', 'Fixed', 'Changed', 'Removed')


def git(repo, *args, allow_failure=False):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                            text=True, encoding='utf-8', errors='replace')
    if result.returncode and not allow_failure:
        raise ValueError(result.stderr.strip() or 'Git command failed')
    return result


def category(subject):
    conventional = re.match(r'^([a-z]+)(?:\([^)]*\))?!?:\s*(.*)$', subject, re.I)
    kind, message = conventional.groups() if conventional else ('', subject)
    if kind.lower() in ('remove', 'removed', 'delete', 'drop') or re.match(
            r'^(remove[ds]?|delet(?:e[ds]?|ion)|drop(?:ped|s)?)\b', message, re.I):
        return 'Removed'
    if kind.lower() in ('feat', 'feature', 'add') or re.match(r'^add(?:ed|s)?\b', message, re.I):
        return 'Added'
    if kind.lower() in ('fix', 'bugfix', 'revert') or re.match(r'^fix(?:ed|es)?\b', message, re.I):
        return 'Fixed'
    return 'Changed'


def markdown(text):
    text = ''.join(c if c.isprintable() else ' ' for c in text)
    return re.sub(r'([\\`*_{}\[\]<>])', r'\\\1', text)


def generate(repo, since=None):
    repo = Path(repo).resolve()
    git(repo, 'rev-parse', '--show-toplevel')
    head = git(repo, 'rev-parse', '--verify', 'HEAD^{commit}').stdout.strip()
    if git(repo, 'rev-parse', '--is-shallow-repository').stdout.strip() == 'true':
        raise ValueError('Shallow history cannot establish a complete changelog. Run git fetch --unshallow first.')
    if since is None:
        tag = git(repo, 'describe', '--tags', '--abbrev=0', head, allow_failure=True)
        since = tag.stdout.strip() if tag.returncode == 0 else None
    boundary = None
    if since is not None:
        boundary = git(repo, 'rev-parse', '--verify', '--end-of-options', since + '^{commit}').stdout.strip()
        git(repo, 'merge-base', '--is-ancestor', boundary, head)
    history = git(repo, 'log', '--no-merges', '--reverse', '--format=%H%x00%s',
                  (boundary + '..' if boundary else '') + head).stdout
    sections = {name: [] for name in CATEGORIES}
    # Git separates records with LF; Unicode separators can be subject text.
    for record in history.split('\n'):
        if not record:
            continue
        commit, subject = record.split('\0', 1)
        sections[category(subject)].append(f'- {markdown(subject)} (`{commit[:12]}`)')
    label = f'Commits since {markdown(since)}' if since else 'All reachable commits (no release tags)'
    lines = ['# Changelog', '', '## [Unreleased]', '', label + '.', '']
    for name, entries in sections.items():
        lines += ['### ' + name, '', *(entries or ['- No changes.']), '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.', help='Git repository (default: current directory)')
    parser.add_argument('--since', help='Explicit ancestor tag or ref; default: nearest reachable tag')
    parser.add_argument('--output', default='CHANGELOG.md', help='Output path, relative to --repo unless absolute')
    parser.add_argument('--force', action='store_true', help='Replace an existing output file')
    args = parser.parse_args()
    try:
        repo = Path(args.repo).resolve()
        output = Path(args.output)
        if not output.is_absolute():
            output = repo / output
        contents = generate(repo, args.since)
        with output.open('w' if args.force else 'x', encoding='utf-8', newline='\n') as stream:
            stream.write(contents)
        print(f'Wrote {output}')
        return 0
    except (ValueError, OSError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
