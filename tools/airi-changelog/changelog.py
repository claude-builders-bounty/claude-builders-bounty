"""Generate a deterministic changelog from local Git history. Python 3.9+."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                            encoding='utf-8', errors='replace')
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Git command failed')
    return result.stdout.strip()


def classify(subject):
    match = re.match(r'^(\w+)(?:\([^\r\n)]*\))?!?:\s*(.*)$', subject)
    kind, text = (match.group(1).lower(), match.group(2)) if match else ('', subject)
    known = {'feat', 'add', 'fix', 'remove', 'removed', 'revert', 'chore', 'docs', 'refactor', 'perf', 'test', 'style', 'build', 'ci'}
    if kind not in known:
        kind, text = '', subject
    if not text:
        text = subject
    category = {'feat': 'Added', 'add': 'Added', 'fix': 'Fixed',
                'remove': 'Removed', 'removed': 'Removed', 'revert': 'Changed'}.get(kind, 'Changed')
    if not kind:
        if re.match(r'^(remove[ds]?|delete[ds]?|drop(?:ped|s)?)\b', text, re.I):
            category = 'Removed'
        elif re.match(r'^(add(?:ed|s)?|introduce[ds]?)\b', text, re.I):
            category = 'Added'
        elif re.match(r'^(fix(?:ed|es)?|resolve[ds]?|repair(?:ed|s)?)\b', text, re.I):
            category = 'Fixed'
    return category, text


def escape(text):
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'([\\`*_\[\]#])', r'\\\1', text)


def generate(repo, since=None):
    git(repo, 'rev-parse', '--verify', 'HEAD')
    shallow = git(repo, 'rev-parse', '--is-shallow-repository')
    if shallow == 'true':
        raise ValueError('Shallow history: fetch full history and tags before generating a changelog.')
    baseline = since
    if baseline is None:
        try:
            baseline = git(repo, 'describe', '--tags', '--abbrev=0', 'HEAD')
        except ValueError:
            baseline = None
    # Resolve user input to an object ID before using it as a revision argument.
    oid = git(repo, 'rev-parse', '--verify', '--end-of-options', baseline + '^{commit}') if baseline else None
    revision = oid + '..HEAD' if oid else 'HEAD'
    history = git(repo, 'log', '--no-merges', '--reverse', '--format=%H%x00%s', revision, '--')
    groups = {name: [] for name in ('Added', 'Fixed', 'Changed', 'Removed')}
    count = 0
    for line in history.split('\n'):
        if not line:
            continue
        sha, subject = line.split('\0', 1)
        category, text = classify(subject)
        groups[category].append(f'- {escape(text)} (`{sha[:12]}`)')
        count += 1
    scope = f'Commits after {escape(baseline)} ({oid[:12]}).' if baseline else 'All commits (no reachable tag).'
    lines = ['# Changelog', '', '## Unreleased', '', scope, '']
    if not count:
        lines += ['No changes since the baseline.', '']
    for category, items in groups.items():
        if items:
            lines += [f'### {category}', '', *items, '']
    return '\n'.join(lines), baseline, count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.')
    parser.add_argument('--since', help='Git revision to use instead of the latest reachable tag')
    parser.add_argument('--output', default='CHANGELOG.md')
    parser.add_argument('--force', action='store_true', help='Explicitly replace an existing output')
    args = parser.parse_args()
    try:
        text, baseline, count = generate(args.repo, args.since)
        output = Path(args.output)
        if output.exists() and not args.force:
            raise ValueError('Output already exists; choose another path or explicitly use --force.')
        if not output.parent.is_dir():
            raise ValueError('Output directory does not exist.')
        if args.force:
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                                 dir=output.parent, delete=False) as handle:
                    temporary = handle.name
                    handle.write(text)
                os.replace(temporary, output)
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
        else:
            with output.open('x', encoding='utf-8', newline='\n') as handle:
                handle.write(text)
        print(f'Generated {output}: {count} commits; baseline={baseline or "full history"}')
    except (ValueError, OSError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
