#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

LAST_TAG=""
if LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LAST_TAG}..HEAD"
  HEADER_TAG="${LAST_TAG}"
else
  RANGE="HEAD"
  HEADER_TAG="initial commit"
fi

python3 - "$OUT_FILE" "$RANGE" "$HEADER_TAG" <<'PY'
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

out_file = Path(sys.argv[1])
range_spec = sys.argv[2]
header_tag = sys.argv[3]

cmd = [
    'git', 'log', '--reverse',
    '--pretty=format:%H%x1f%s%x1f%b%x1e',
]
if range_spec != 'HEAD':
    cmd.append(range_spec)

raw = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
records = [r for r in raw.split('\x1e') if r.strip()]

sections = OrderedDict([
    ('Added', []),
    ('Fixed', []),
    ('Changed', []),
    ('Removed', []),
])

prefix_re = re.compile(r'^(?:feat|fix|docs|refactor|test|chore|perf|ci|build|style|revert)(?:\([^)]+\))?:\s*', re.I)

for rec in records:
    sha, subject, body = (rec.split('\x1f', 2) + ['', ''])[:3]
    sha = sha.strip()
    subject = subject.strip()
    body = body.strip()
    short_sha = sha[:7]
    combined = f'{subject}\n{body}'.lower()

    clean_subject = prefix_re.sub('', subject).strip() or subject

    if re.match(r'^(feat|add|new|create|introduce)\b', subject, re.I) or 'add ' in combined:
        section = 'Added'
    elif re.match(r'^(fix|bug|hotfix|patch|resolve)\b', subject, re.I) or any(k in combined for k in [' fixed ', ' bug ', ' error ', ' issue ']):
        section = 'Fixed'
    elif re.match(r'^(remove|delete|drop|deprecate)\b', subject, re.I) or any(k in combined for k in [' remove ', ' delete ', ' drop ', ' deprecate ']):
        section = 'Removed'
    else:
        section = 'Changed'

    sections[section].append(f'- {clean_subject} (`{short_sha}`)')

lines = [
    '# CHANGELOG',
    '',
    f'_Generated from commits since `{header_tag}`_',
    '',
]

for name, items in sections.items():
    if not items:
        continue
    lines.extend([f'## {name}', ''])
    lines.extend(items)
    lines.append('')

if all(not items for items in sections.values()):
    lines.extend(['## Changed', '', '- No commits found in the selected range.', ''])

out_file.write_text('\n'.join(lines).rstrip() + '\n')
print(out_file)
PY
