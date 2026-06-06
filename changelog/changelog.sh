#!/usr/bin/env bash
# CHANGELOG Generator — structured changelog from git history
# Usage: ./changelog.sh [--since <tag>] [--output CHANGELOG.md]

set -euo pipefail

OUTPUT="${OUTPUT:-CHANGELOG.md}"
SINCE_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE_TAG="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not a git repository" >&2
  exit 1
fi

# Determine the starting point
if [ -z "$SINCE_TAG" ]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -n "$SINCE_TAG" ]; then
  RANGE="$SINCE_TAG..HEAD"
  echo "→ Generating changelog since tag: $SINCE_TAG"
else
  RANGE=""
  echo "→ Generating changelog from all commits (no previous tag)"
fi

# Fetch commits
COMMITS=$(git log "$RANGE" --pretty=format:"%s" 2>/dev/null || git log --pretty=format:"%s")

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -z "$line" ] && continue

  msg=$(echo "$line" | sed 's/^[^:]*: //')

  if echo "$line" | grep -qiE '^(feat|add|Added|Add|FEAT)'; then
    ADDED="$ADDED- $msg\n"
  elif echo "$line" | grep -qiE '^(fix|bug|hotfix|FIX)'; then
    FIXED="$FIXED- $msg\n"
  elif echo "$line" | grep -qiE '^(remove|drop|delete|REMOVE)'; then
    REMOVED="$REMOVED- $msg\n"
  else
    CHANGED="$CHANGED- $msg\n"
  fi
done <<< "$COMMITS"

# Get today's date and version
TODAY=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")

# Generate output
{
  echo "# Changelog"
  echo ""
  echo "## [$VERSION] — $TODAY"
  echo ""

  if [ -n "$ADDED" ]; then
    echo "### Added"
    echo -e "$ADDED"
  fi

  if [ -n "$FIXED" ]; then
    echo "### Fixed"
    echo -e "$FIXED"
  fi

  if [ -n "$CHANGED" ]; then
    echo "### Changed"
    echo -e "$CHANGED"
  fi

  if [ -n "$REMOVED" ]; then
    echo "### Removed"
    echo -e "$REMOVED"
  fi

  # Commit count summary
  TOTAL=$(echo "$COMMITS" | grep -c . 2>/dev/null || echo 0)
  echo ""
  echo "---"
  echo ""
  echo "_${TOTAL} commits since ${SINCE_TAG:-the beginning}_"
} > "$OUTPUT"

echo "✅ CHANGELOG written to $OUTPUT"
echo "   Run: cat $OUTPUT"
