#!/usr/bin/env bash
set -euo pipefail

# CHANGELOG Generator — generates CHANGELOG.md from git history since last tag
# Usage: bash changelog.sh [--repo path] [--output CHANGELOG.md]

REPO="."
OUTPUT="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

cd "$REPO"

if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: not a git repository"
  exit 1
fi

LAST_TAG=$(git describe --tags --abbrev=0 2> /dev/null || echo "")

if [[ -z "$LAST_TAG" ]]; then
  echo "Warning: no tags found, using all commits"
  COMMITS=$(git log --oneline --no-decorate HEAD 2> /dev/null || true)
else
  COMMITS=$(git log --oneline --no-decorate "$LAST_TAG..HEAD" 2> /dev/null || true)
fi

if [[ -z "$COMMITS" ]]; then
  echo "# Changelog" > "$OUTPUT"
  echo "" >> "$OUTPUT"
  echo "No new commits since last release." >> "$OUTPUT"
  echo "Generated empty CHANGELOG.md"
  exit 0
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
INTERNAL=""

while IFS= read -r line; do
  SHA=$(echo "$line" | awk '{print $1}')
  MSG=$(echo "$line" | cut -d' ' -f2-)

  if echo "$MSG" | grep -qiE "^feat(\([^)]*\))?:"; then
    ADDED="$ADDED\n- $MSG"
  elif echo "$MSG" | grep -qiE "^fix(\([^)]*\))?:"; then
    FIXED="$FIXED\n- $MSG"
  elif echo "$MSG" | grep -qiE "^(BREAKING[ -]CHANGE|refactor|perf)(\([^)]*\))?:"; then
    CHANGED="$CHANGED\n- $MSG"
  elif echo "$MSG" | grep -qiE "^revert(\([^)]*\))?:"; then
    REMOVED="$REMOVED\n- $MSG"
  elif echo "$MSG" | grep -qiE "^(chore|docs|test|style|build|ci)(\([^)]*\))?:"; then
    INTERNAL="$INTERNAL\n- $MSG"
  else
    # Keyword fallback for non-conventional commits
    if echo "$MSG" | grep -qiE "\\b(add|create|implement|introduce|new|support)\\b"; then
      ADDED="$ADDED\n- $MSG"
    elif echo "$MSG" | grep -qiE "\\b(fix|patch|correct|resolve|hotfix|bug|repair)\\b"; then
      FIXED="$FIXED\n- $MSG"
    elif echo "$MSG" | grep -qiE "\\b(change|update|upgrade|migrate|refactor|redesign)\\b"; then
      CHANGED="$CHANGED\n- $MSG"
    elif echo "$MSG" | grep -qiE "\\b(remove|delete|drop|deprecate|revert|cleanup)\\b"; then
      REMOVED="$REMOVED\n- $MSG"
    else
      INTERNAL="$INTERNAL\n- $MSG"
    fi
  fi
done <<< "$COMMITS"

DATE=$(date +%Y-%m-%d)
VERSION="${LAST_TAG:-0.1.0}"

{
  echo "# Changelog"
  echo ""
  echo "## [$VERSION] - $DATE"
  echo ""

  if [[ -n "$ADDED" ]]; then
    echo "### Added"
    echo -e "$ADDED" | grep -v '^$'
    echo ""
  fi

  if [[ -n "$FIXED" ]]; then
    echo "### Fixed"
    echo -e "$FIXED" | grep -v '^$'
    echo ""
  fi

  if [[ -n "$CHANGED" ]]; then
    echo "### Changed"
    echo -e "$CHANGED" | grep -v '^$'
    echo ""
  fi

  if [[ -n "$REMOVED" ]]; then
    echo "### Removed"
    echo -e "$REMOVED" | grep -v '^$'
    echo ""
  fi

  if [[ -n "$INTERNAL" ]]; then
    echo "### Internal"
    echo -e "$INTERNAL" | grep -v '^$'
    echo ""
  fi
} > "$OUTPUT"

echo "Generated CHANGELOG.md with $(echo "$COMMITS" | wc -l) entries"
