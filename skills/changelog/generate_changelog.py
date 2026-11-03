#!/usr/bin/env python3
"""Deterministic, dependency-free changelog generation; no repository code execution."""
from __future__ import annotations

import argparse
import difflib
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

START = '<!-- generated-changelog:start -->'
END = '<!-- generated-changelog:end -->'
SECTIONS = ('Added', 'Fixed', 'Changed', 'Removed')
HEADER = ('# Changelog\n\nAll notable changes to this project are documented here.\n'
          'The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n')
CONVENTIONAL = re.compile(r'^([A-Za-z][A-Za-z0-9_-]*)(?:\(([^)\n]+)\))?(!)?:[ \t]*(.+)$')


class ChangelogError(Exception):
    pass


def git(repo: Path, *args: str, allow_failure: bool = False) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.update(GIT_PAGER='cat', GIT_TERMINAL_PROMPT='0', GIT_NO_REPLACE_OBJECTS='1')
    result = subprocess.run(['git', '-C', str(repo), *args], env=env,
                            capture_output=True, timeout=60)
    if result.returncode and not allow_failure:
        raise ChangelogError('Git inspection failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result


def resolve(repo: Path, ref: str) -> str:
    if not ref or ref.startswith('-'):
        raise ChangelogError('A ref must be nonempty and must not start with an option prefix.')
    result = git(repo, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}')
    sha = result.stdout.decode('ascii').strip()
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', sha):
        raise ChangelogError('Git returned an invalid object identifier.')
    return sha


def escape_markdown(value: str) -> str:
    # Do not emit terminal controls, active HTML, or executable links from commit text.
    value = ' '.join(value.split())
    value = ''.join(c for c in value if ord(c) >= 32 and ord(c) != 127)
    value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'([\\`*_[\]{}|])', r'\\\1', value)


def classify(subject: str, body: str) -> tuple[str, str, bool] | None:
    match = CONVENTIONAL.match(subject)
    kind, scope, bang, description = (match.groups() if match else ('', None, None, subject))
    kind = kind.lower()
    breaking = bool(bang or re.search(r'(?m)^BREAKING[ -]CHANGE:[ \t]*', body))
    if kind in {'chore', 'ci', 'style', 'test', 'tests'} and not breaking:
        return None
    if kind in {'remove', 'removed', 'delete'} or re.match(r'(?i)^(remove|delete|drop)\b', description):
        section, verb = 'Removed', 'Remove'
    elif kind == 'feat' or (not kind and re.match(r'(?i)^(add|introduce)\b', description)):
        section, verb = 'Added', 'Add'
    elif kind in {'fix', 'bugfix'} or (not kind and re.match(r'(?i)^(fix|repair|resolve)\b', description)):
        section, verb = 'Fixed', 'Fix'
    else:
        section, verb = 'Changed', 'Update'
    # Keep the original meaning. This is a rule-based summary, not inferred release claims.
    starts_with_verb = re.match(r'(?i)^(add|fix|update|remove|delete|drop|introduce|improve|change|support|handle|avoid|reduce|revert|document|deprecate)\b', description)
    if not starts_with_verb:
        description = verb + ' ' + description
    detail = escape_markdown(description)
    if scope:
        detail = '**' + escape_markdown(scope) + '**: ' + detail
    if breaking:
        detail = '**BREAKING** ' + detail
    return section, detail, breaking


def collect(repo: Path, start_ref: str | None, to_ref: str) -> dict[str, list[str]]:
    end_sha = resolve(repo, to_ref)
    if start_ref is None:
        result = git(repo, 'describe', '--tags', '--abbrev=0', end_sha, allow_failure=True)
        start_ref = result.stdout.decode('utf-8', 'replace').strip() if result.returncode == 0 else None
    if start_ref:
        start_sha = resolve(repo, start_ref)
        if git(repo, 'merge-base', '--is-ancestor', start_sha, end_sha, allow_failure=True).returncode:
            raise ChangelogError('The from-ref must be an ancestor of the to-ref.')
        selected = start_sha + '..' + end_sha
    else:
        if git(repo, 'rev-parse', '--is-shallow-repository').stdout.strip() == b'true':
            raise ChangelogError('No reachable tag in a shallow clone; fetch complete history or provide an available --from ref.')
        selected = end_sha
    # Commit messages cannot contain NUL. Three NUL-delimited fields per commit,
    # with -z delimiting records, preserve pipes/newlines/END markers safely.
    raw = git(repo, 'log', '--no-merges', '--reverse', '-z', '--format=%H%x00%s%x00%b', selected, '--').stdout
    fields = raw.split(b'\0')
    if fields and fields[-1] == b'':
        fields.pop()
    if len(fields) % 3:
        raise ChangelogError('Unexpected git-log framing; refusing partial output.')
    sections: dict[str, list[str]] = {section: [] for section in SECTIONS}
    for i in range(0, len(fields), 3):
        sha, subject, body = (field.decode('utf-8', 'replace') for field in fields[i:i + 3])
        item = classify(subject, body)
        if item:
            section, detail, _ = item
            sections[section].append('- ' + detail + ' (`' + sha[:12] + '`)')
    return sections


def update_document(old: str, sections: dict[str, list[str]]) -> str:
    newline = '\r\n' if '\r\n' in old else '\n'
    blocks = []
    for section in SECTIONS:
        if sections[section]:
            blocks.append('### ' + section + '\n' + '\n'.join(sections[section]))
    content = '\n\n'.join(blocks) or '_No user-facing changes in the selected range._'
    managed = (START + '\n\n' + content + '\n\n' + END).replace('\n', newline)
    document = old or HEADER.replace('\n', newline)
    heading = re.search(r'^##[ \t]+\[Unreleased\][^\r\n]*(?:\r?\n|$)', document, re.M | re.I)
    if not heading:
        # Insert before first release, preserving every historical byte.
        first_release = re.search(r'^##[ \t]+', document, re.M)
        position = first_release.start() if first_release else len(document)
        prefix = document[:position]
        if prefix and not prefix.endswith(newline * 2):
            prefix += newline if prefix.endswith(newline) else newline * 2
        return prefix + '## [Unreleased]' + newline * 2 + managed + newline * 2 + document[position:]
    next_release = re.search(r'^##[ \t]+', document[heading.end():], re.M)
    end = heading.end() + next_release.start() if next_release else len(document)
    section = document[heading.end():end]
    if START in section or END in section:
        if section.count(START) != 1 or section.count(END) != 1 or section.index(START) > section.index(END):
            raise ChangelogError('Malformed generated block; refusing to change manual content.')
        section = section[:section.index(START)] + managed + section[section.index(END) + len(END):]
    else:
        section = newline + managed + newline * 2 + section
    return document[:heading.end()] + section + document[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--from', dest='from_ref', help='Exclusive starting ref; defaults to nearest reachable tag')
    parser.add_argument('--to', default='HEAD', help='Inclusive ending ref; defaults to HEAD')
    parser.add_argument('--output', type=Path, help='Output path relative to current directory; default is repository/CHANGELOG.md')
    parser.add_argument('--dry-run', action='store_true', help='Print the full proposed document without writing')
    args = parser.parse_args()
    try:
        repo = args.repo.resolve(strict=True)
        gitdir = Path(git(repo, 'rev-parse', '--absolute-git-dir').stdout.decode().strip()).resolve()
        common = Path(git(repo, 'rev-parse', '--git-common-dir').stdout.decode().strip())
        common = (common if common.is_absolute() else repo / common).resolve()
        bare = git(repo, 'rev-parse', '--is-bare-repository').stdout.strip() == b'true'
        root = repo if bare else Path(git(repo, 'rev-parse', '--show-toplevel').stdout.decode().strip())
        output = args.output if args.output is not None else root / 'CHANGELOG.md'
        if output.is_symlink():
            raise ChangelogError('Refusing a symlink output path.')
        output = output.resolve()
        if (output == gitdir or gitdir in output.parents
                or output == common or common in output.parents or output == root / '.git'):
            raise ChangelogError('Refusing to write inside Git metadata; pass an external --output for a bare repo.')
        old_bytes = output.read_bytes() if output.exists() else b''
        old = old_bytes.decode('utf-8')
        new = update_document(old, collect(repo, args.from_ref, args.to))
        if args.dry_run:
            sys.stdout.write(new)
            return 0
        encoded = new.encode('utf-8')
        if encoded == old_bytes:
            print('CHANGELOG unchanged.')
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(prefix='.changelog-', dir=output.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, stat.S_IMODE(output.stat().st_mode) if output.exists() else 0o644)
            os.replace(temporary, output)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        sys.stdout.writelines(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                                 fromfile='before/CHANGELOG.md', tofile='after/CHANGELOG.md'))
        return 0
    except (ChangelogError, OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        print('error: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
