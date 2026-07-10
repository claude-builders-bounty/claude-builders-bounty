#!/usr/bin/env bash
# generate-changelog.sh — Generate a structured CHANGELOG.md from git history.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || { echo "Error: Not a git repository" >&2; exit 1; })"
cd "$REPO_ROOT"

FROM_TAG=""
ALL_HISTORY=false
OUTPUT_FILE="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)   FROM_TAG="$2"; shift 2;;
    --all)    ALL_HISTORY=true; shift;;
    -o|--output) OUTPUT_FILE="$2"; shift 2;;
    -h|--help) echo "Usage: generate-changelog.sh [--from TAG] [--all] [-o FILE]"; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 1;;
  esac
done

# Determine the commit range
LAST_TAG=""
if [[ "$ALL_HISTORY" == "true" ]]; then
  RANGE=""
elif [[ -n "$FROM_TAG" ]]; then
  RANGE="${FROM_TAG}..HEAD"
else
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"
  if [[ -n "$LAST_TAG" ]]; then
    RANGE="${LAST_TAG}..HEAD"
  else
    RANGE=""
  fi
fi

if [[ -n "$RANGE" ]]; then
  COMMITS=$(git log "$RANGE" --pretty=format:"%H|%s" --reverse)
else
  COMMITS=$(git log --pretty=format:"%H|%s" --reverse)
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found in the specified range."
  exit 0
fi

# Use python3 for the parsing and generation
echo "$COMMITS" | python3 -c "
import sys, re, os
from datetime import date

lines = [l.strip() for l in sys.stdin if l.strip()]

added, fixed, changed, removed, other = [], [], [], [], []

for line in lines:
    parts = line.split('|', 1)
    if len(parts) != 2:
        continue
    full_hash, subject = parts
    short_hash = full_hash[:7]

    # Try conventional commit: type(scope): description
    m = re.match(r'^([a-z]+)\(([^)]+)\):\s+(.+)$', subject)
    if m:
        ctype, scope, desc = m.group(1), m.group(2), m.group(3)
    else:
        m2 = re.match(r'^([a-z]+):\s+(.+)$', subject)
        if m2:
            ctype, desc = m2.group(1), m2.group(2)
            scope = ''
        else:
            # Keyword fallback
            desc = subject
            scope = ''
            lower = subject.lower()
            if re.match(r'^(add|added|adding|new|create|created|implement|introduce)', lower):
                ctype = 'feat'
            elif re.match(r'^(fix|fixed|fixing|bugfix|patch|hotfix|repair)', lower):
                ctype = 'fix'
            elif re.match(r'^(remove|removed|removing|delete|deleted|drop|dropped)', lower):
                ctype = 'remove'
            elif re.match(r'^(refactor|change|changed|update|updated|modify|modified|rename|renamed|move|moved)', lower):
                ctype = 'refactor'
            else:
                ctype = 'other'

    if scope:
        entry = f'- {desc} (\`{scope}\`, \`{short_hash}\`)'
    else:
        entry = f'- {desc} (\`{short_hash}\`)'

    if ctype == 'feat':
        added.append(entry)
    elif ctype == 'fix':
        fixed.append(entry)
    elif ctype == 'refactor':
        changed.append(entry)
    elif ctype in ('remove', 'revert'):
        removed.append(entry)
    else:
        other.append(entry)

# Build the header
import os
all_hist = os.environ.get('ALL_HISTORY', 'false') == 'true'
from_tag = os.environ.get('FROM_TAG', '')
last_tag = os.environ.get('LAST_TAG', '')

if all_hist:
    header = '## [Full History]'
elif from_tag:
    header = f'## [Changes since {from_tag}]'
else:
    tag_label = last_tag if last_tag else 'Unreleased'
    header = f'## [{tag_label}] - {date.today().isoformat()}'

print('# Changelog')
print()
print('All notable changes to this project are documented in this file.')
print()
print(header)
print()

if added:
    print('### Added')
    for e in added: print(e)
    print()
if fixed:
    print('### Fixed')
    for e in fixed: print(e)
    print()
if changed:
    print('### Changed')
    for e in changed: print(e)
    print()
if removed:
    print('### Removed')
    for e in removed: print(e)
    print()
if other:
    print('### Other')
    for e in other: print(e)
    print()

import sys
print(f'Generated with: Added={len(added)}, Fixed={len(fixed)}, Changed={len(changed)}, Removed={len(removed)}, Other={len(other)}', file=sys.stderr)
" ALL_HISTORY="$ALL_HISTORY" FROM_TAG="$FROM_TAG" LAST_TAG="$LAST_TAG" > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE"
