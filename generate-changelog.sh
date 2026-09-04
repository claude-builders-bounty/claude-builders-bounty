#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

if [ -z "$LAST_TAG" ]; then
  echo "Error: No commits found in repository" >&2
  exit 1
fi

DATE=$(date +%Y-%m-%d)
TMPFILE=$(mktemp)
trap "rm -f $TMPFILE" EXIT

git log "${LAST_TAG}..HEAD" --pretty=format:"%h %s" --no-merges > "$TMPFILE"

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line || [ -n "$line" ]; do
  [ -z "$line" ] && continue
  MSG="${line#* }"
  [ -z "$MSG" ] && continue
  
  TYPE="other"
  DESC="$MSG"
  
  if [[ "$MSG" =~ ^([a-zA-Z]+)\(.+\):[[:space:]]*(.*) ]]; then
    TYPE="${BASH_REMATCH[1]}"
    DESC="${BASH_REMATCH[2]}"
  elif [[ "$MSG" =~ ^([a-zA-Z]+):[[:space:]]*(.*) ]]; then
    TYPE="${BASH_REMATCH[1]}"
    DESC="${BASH_REMATCH[2]}"
  fi
  
  case "$TYPE" in
    feat)         ADDED="${ADDED}- ${DESC}"$'\n' ;;
    fix)          FIXED="${FIXED}- ${DESC}"$'\n' ;;
    refactor|style|perf|change) CHANGED="${CHANGED}- ${DESC}"$'\n' ;;
    revert|remove|delete)       REMOVED="${REMOVED}- ${DESC}"$'\n' ;;
    docs|test|ci|chore|build)   OTHER="${OTHER}- ${DESC}"$'\n' ;;
    *)            OTHER="${OTHER}- ${MSG}"$'\n' ;;
  esac
done < "$TMPFILE"

{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased] - ${DATE}"
  echo ""
  
  if [ -n "$ADDED" ]; then
    echo "### Added"
    printf "%s" "$ADDED"
    echo ""
  fi
  
  if [ -n "$FIXED" ]; then
    echo "### Fixed"
    printf "%s" "$FIXED"
    echo ""
  fi
  
  if [ -n "$CHANGED" ]; then
    echo "### Changed"
    printf "%s" "$CHANGED"
    echo ""
  fi
  
  if [ -n "$REMOVED" ]; then
    echo "### Removed"
    printf "%s" "$REMOVED"
    echo ""
  fi
  
  if [ -n "$OTHER" ]; then
    echo "### Other"
    printf "%s" "$OTHER"
    echo ""
  fi
} > "$OUTPUT"

echo "Generated $OUTPUT successfully"
