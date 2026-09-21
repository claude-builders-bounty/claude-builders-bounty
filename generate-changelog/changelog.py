"""Generate a deterministic, local-only changelog using Git and Python 3."""
import argparse
from pathlib import Path
import re
import subprocess
import sys

CATEGORIES = ('Added', 'Fixed', 'Changed', 'Removed')

def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout.decode('utf-8', errors='replace').strip()

def categorize(subject):
    conventional = re.match(r'^(\w+)(?:\([^)]*\))?(!)?:\s*(.*)$', subject)
    kind = conventional.group(1).lower() if conventional else ''
    description = conventional.group(3) if conventional else subject
    first_word = description.split(maxsplit=1)[0].lower() if description else ''
    if kind in ('remove', 'removed') or first_word in ('remove', 'removed', 'delete', 'deleted', 'drop', 'dropped'):
        section = 'Removed'
    elif kind in ('feat', 'feature', 'add') or first_word in ('add', 'added', 'introduce', 'introduces'):
        section = 'Added'
    elif kind in ('fix', 'bugfix', 'revert') or first_word in ('fix', 'fixed', 'repair', 'resolve'):
        section = 'Fixed'
    else:
        section = 'Changed'
    if conventional and conventional.group(2):
        description = 'BREAKING: ' + description
    return section, description

def generate(repo):
    head = git(repo, 'rev-parse', '--verify', 'HEAD')
    if git(repo, 'rev-parse', '--is-shallow-repository') == 'true':
        raise ValueError('Shallow history: fetch full history and tags before generating.')
    try:
        base = git(repo, 'describe', '--tags', '--abbrev=0', head)
    except ValueError:
        base = None
    revision = git(repo, 'rev-parse', '--verify', base + '^{commit}') + '..' + head if base else head
    records = git(repo, 'log', '--reverse', '--no-merges', '--format=%H%x00%s', revision, '--')
    grouped = {category: [] for category in CATEGORIES}
    for record in records.splitlines():
        if not record:
            continue
        sha, subject = record.split('\0', 1)
        section, description = categorize(subject)
        # Escape Markdown/HTML so commit text stays inert and readable.
        description = description.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        description = re.sub(r'([\\`*_\[\]])', r'\\\1', description)
        grouped[section].append(f'- {description} (`{sha[:12]}`)')
    lines = ['# Changelog', '', '## [Unreleased]', '']
    for category in CATEGORIES:
        if grouped[category]:
            lines += ['### ' + category, '', *grouped[category], '']
    if not any(grouped.values()):
        lines += ['No changes since the latest tag.', '']
    return '\n'.join(lines), base, head

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, default=Path('CHANGELOG.md'))
    args = parser.parse_args()
    try:
        content, base, head = generate(args.repo)
        # Exclusive creation prevents accidental loss of existing release notes.
        with args.output.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
        print(f'Created {args.output}; base={base or "entire history"}; head={head}')
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Changelog not written: {exc}\n')

if __name__ == '__main__':
    main()
