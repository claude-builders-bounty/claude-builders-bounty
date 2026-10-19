#!/usr/bin/env bash
# Standalone structured CHANGELOG generator
set -euo pipefail

TARGET_FILE="CHANGELOG.md"
VERSION="${1:-Unreleased}"
DATE=$(date +'%Y-%m-%d')

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
RANGE="HEAD"
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  echo "Generating changelog from $LAST_TAG to HEAD..."
else
  echo "No previous tags found. Generating from entire commit history..."
fi

COMMITS=$(git log "$RANGE" --pretty=format:"%s" 2>/dev/null || true)

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  [ -z "$line" ] && continue
  if [[ "$line" =~ ^(feat|add)(\(.*\))?:\ (.*) ]]; then
    ADDED="${ADDED}
- ${BASH_REMATCH[3]}"
  elif [[ "$line" =~ ^(fix|bug)(\(.*\))?:\ (.*) ]]; then
    FIXED="${FIXED}
- ${BASH_REMATCH[3]}"
  elif [[ "$line" =~ ^(remove|delete)(\(.*\))?:\ (.*) ]]; then
    REMOVED="${REMOVED}
- ${BASH_REMATCH[3]}"
  elif [[ "$line" =~ ^(refactor|perf|change|chore|update)(\(.*\))?:\ (.*) ]]; then
    CHANGED="${CHANGED}
- ${BASH_REMATCH[3]}"
  else
    CHANGED="${CHANGED}
- $line"
  fi
done <<< "$COMMITS"

NEW_ENTRY="## [$VERSION] - $DATE
"

if [ -n "$ADDED" ]; then
  NEW_ENTRY="${NEW_ENTRY}
### Added${ADDED}
"
fi
if [ -n "$FIXED" ]; then
  NEW_ENTRY="${NEW_ENTRY}
### Fixed${FIXED}
"
fi
if [ -n "$CHANGED" ]; then
  NEW_ENTRY="${NEW_ENTRY}
### Changed${CHANGED}
"
fi
if [ -n "$REMOVED" ]; then
  NEW_ENTRY="${NEW_ENTRY}
### Removed${REMOVED}
"
fi

echo -e "$NEW_ENTRY"
