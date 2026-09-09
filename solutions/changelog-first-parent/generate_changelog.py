"""Generate a reviewable Unreleased section using local Git history only."""

import argparse
import html
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

START = '<!-- changelog-generator:start -->'
END = '<!-- changelog-generator:end -->'
CATEGORIES = ('Added', 'Fixed', 'Changed', 'Removed')


def git(repo, *args, optional=False):
    result = subprocess.run(
        ['git', '-C', str(repo), '--no-pager', *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode:
        if optional:
            return None
        raise ValueError('Git command failed: ' + ' '.join(args))
    return result.stdout.decode('utf-8', errors='replace')


def literal(text):
    text = ''.join(c if c.isprintable() else ' ' for c in text)
    return re.sub(r'([\\`*_[\]{}()#!|])', r'\\\1', html.escape(text, quote=False))


def category(subject):
    match = re.match(r'^([a-z]+)(?:\([^)]*\))?!?:\s*', subject, re.I)
    kind = match.group(1).lower() if match else ''
    if kind in ('feat', 'add'):
        return 'Added'
    if kind == 'fix':
        return 'Fixed'
    if kind in ('remove', 'removed', 'delete'):
        return 'Removed'
    first = re.match(r'^([a-z]+)\b', subject, re.I)
    verb = first.group(1).lower() if first else ''
    if not match and verb in ('add', 'added', 'introduce'):
        return 'Added'
    if not match and verb in ('fix', 'fixed', 'repair'):
        return 'Fixed'
    if not match and verb in ('remove', 'removed', 'delete'):
        return 'Removed'
    return 'Changed'


def generate(repo):
    head = git(repo, 'rev-parse', '--verify', 'HEAD^{commit}').strip()
    if git(repo, 'rev-parse', '--is-shallow-repository').strip() != 'false':
        raise ValueError('Shallow history is incomplete; fetch full history and tags first.')
    tag = git(repo, 'describe', '--tags', '--first-parent', '--abbrev=0', head, optional=True)
    if tag is None:
        # A missing tag is valid; a broken tag lookup must not select all history.
        tags = git(repo, 'tag', '--merged', head).strip()
        parents = set(git(repo, 'rev-list', '--first-parent', head).splitlines())
        for name in tags.splitlines():
            if git(repo, 'rev-parse', '--verify', name + '^{commit}').strip() in parents:
                raise ValueError('Could not resolve the first-parent release tag.')
        revision = head
        boundary = 'No first-parent release tag; all reachable history.'
    else:
        tag = tag.strip()
        base = git(repo, 'rev-parse', '--verify', tag + '^{commit}').strip()
        revision = base + '..' + head
        boundary = 'Since tag ' + literal(tag) + ' (`' + base + '`).'
    raw = git(repo, 'log', '--reverse', '--topo-order', '-z', '--format=%H%x00%s', revision, '--')
    fields = raw.split('\0')
    if fields[-1] != '' or (len(fields) - 1) % 2:
        raise ValueError('Unexpected Git log framing.')
    grouped = {key: [] for key in CATEGORIES}
    for sha, subject in zip(fields[0:-1:2], fields[1:-1:2]):
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', sha):
            raise ValueError('Unexpected commit identifier.')
        grouped[category(subject)].append('- ' + literal(subject) + ' (`' + sha + '`)')
    lines = [START, '## [Unreleased]', '', boundary, 'Head: `' + head + '`.', '']
    for name, entries in grouped.items():
        lines.extend(['### ' + name, '', *(entries or ['- None.']), ''])
    lines.append(END)
    return '\n'.join(lines) + '\n'


def update(output, section):
    if output.is_symlink():
        raise ValueError('Refusing to replace a symbolic link.')
    old = output.read_bytes() if output.exists() else None
    if old is None:
        content = '# Changelog\n\n' + section
    else:
        text = old.decode('utf-8')
        if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
            raise ValueError('Existing file has no unique managed section; choose a new output path.')
        start, end = text.index(START), text.index(END) + len(END)
        content = text[:start] + section.rstrip('\n') + text[end:]
    encoded = content.encode('utf-8')
    if old == encoded:
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.changelog-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        if old is None:
            # Exclusive publication, including a concurrent file or symlink creator.
            os.link(temporary, output)
        else:
            if output.is_symlink() or output.read_bytes() != old:
                raise ValueError('Output changed during generation; retry after coordinating edits.')
            os.chmod(temporary, stat.S_IMODE(output.stat().st_mode))
            os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path('.'))
    parser.add_argument('--output', type=Path, default=Path('CHANGELOG.md'))
    parser.add_argument('--stdout', action='store_true', help='Preview without writing a file')
    args = parser.parse_args()
    try:
        section = generate(args.repo)
        if args.stdout:
            print('# Changelog\n\n' + section, end='')
        else:
            update(args.output.absolute(), section)
    except (OSError, UnicodeError, ValueError) as exc:
        print('changelog: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
