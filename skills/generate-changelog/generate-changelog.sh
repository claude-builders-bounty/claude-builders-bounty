#!/usr/bin/env bash
# CHANGELOG Generator
# Automatically generates a structured CHANGELOG.md from git history.
#
# Usage:
#   bash generate-changelog.sh
#   bash generate-changelog.sh /path/to/repo
#
# Requirements: git, sed, date

set -euo pipefail

REPO_DIR="${1:-.}"
cd "$REPO_DIR"

if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository" >&2
  exit 1
fi

OUTPUT_FILE="CHANGELOG.md"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
DATE=$(date +%Y-%m-%d)

echo "# Changelog" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "All notable changes to **$REPO_NAME** will be documented in this file." >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Get all tags sorted by version (latest first)
TAGS=$(git tag --sort=-version:refname 2>/dev/null || echo "")

if [ -z "$TAGS" ]; then
  # No tags — generate from all commits
  echo "## [Unreleased] - $DATE" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  generate_section "" "HEAD"
  cat "$OUTPUT_FILE"
  exit 0
fi

# Generate changelog for each tag range
PREV_TAG=""
for TAG in $TAGS; do
  if [ -z "$PREV_TAG" ]; then
    # Latest tag → HEAD
    echo "## [Unreleased] - $DATE" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    generate_section "$TAG" "HEAD"
  else
    # Between tags
    TAG_DATE=$(git log -1 --format=%ai "$TAG" 2>/dev/null | cut -d' ' -f1)
    echo "## [$PREV_TAG] - $TAG_DATE" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    generate_section "$TAG" "$PREV_TAG"
  fi
  echo "" >> "$OUTPUT_FILE"
  PREV_TAG="$TAG"
done

# First tag (oldest)
TAG_DATE=$(git log -1 --format=%ai "$PREV_TAG" 2>/dev/null | cut -d' ' -f1)
echo "## [$PREV_TAG] - $TAG_DATE" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
generate_section "" "$PREV_TAG"

echo "" >> "$OUTPUT_FILE"
cat "$OUTPUT_FILE"

generate_section() {
  local FROM="$1"
  local TO="$2"

  # Get commits in range
  local RANGE
  if [ -z "$FROM" ]; then
    RANGE="$TO"
  else
    RANGE="$FROM..$TO"
  fi

  local COMMITS
  COMMITS=$(git log "$RANGE" --format="%s" --no-merges 2>/dev/null || echo "")

  if [ -z "$COMMITS" ]; then
    echo "  No changes." >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    return
  fi

  # Categorize commits
  local ADDED="" FIXED="" CHANGED="" REMOVED=""

  while IFS= read -r line; do
    # Skip empty lines
    [ -z "$line" ] && continue

    # Categorize based on conventional commit prefixes
    case "$line" in
      feat*|add*|new*|implement*)
        ADDED="${ADDED}- ${line}"$'\n'
        ;;
      fix*|bug*|hotfix*|patch*)
        FIXED="${FIXED}- ${line}"$'\n'
        ;;
      refactor*|chore*|style*|perf*|test*|docs*|ci*|build*)
        CHANGED="${CHANGED}- ${line}"$'\n'
        ;;
      remove*|delete*|drop*)
        REMOVED="${REMOVED}- ${line}"$'\n'
        ;;
      *)
        CHANGED="${CHANGED}- ${line}"$'\n'
        ;;
    esac
  done <<< "$COMMITS"

  # Output sections
  if [ -n "$ADDED" ]; then
    echo "### Added" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "$ADDED" >> "$OUTPUT_FILE"
  fi

  if [ -n "$FIXED" ]; then
    echo "### Fixed" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "$FIXED" >> "$OUTPUT_FILE"
  fi

  if [ -n "$CHANGED" ]; then
    echo "### Changed" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "$CHANGED" >> "$OUTPUT_FILE"
  fi

  if [ -n "$REMOVED" ]; then
    echo "### Removed" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "$REMOVED" >> "$OUTPUT_FILE"
  fi
}
