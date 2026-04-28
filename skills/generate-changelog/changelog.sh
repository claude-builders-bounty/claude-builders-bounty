#!/usr/bin/env bash
set -euo pipefail

CHANGELOG_FILE="CHANGELOG.md"
SINCE_TAG=""

# Find the most recent git tag
SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -n "$SINCE_TAG" ]; then
  COMMIT_RANGE="$SINCE_TAG..HEAD"
  echo "Generating changelog from tag: $SINCE_TAG"
else
  COMMIT_RANGE="HEAD"
  echo "No tags found. Generating changelog from all commits."
fi

TODAY=$(date +%Y-%m-%d)
VERSION="Unreleased"

# If there's a tag, try to derive the next version
if [ -n "$SINCE_TAG" ]; then
  VERSION="$SINCE_TAG..HEAD"
fi

# Collect commits and categorize
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  msg="$line"
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^(feat|add|feature)\b'; then
    ADDED="${ADDED}- ${msg}
"
  elif echo "$lower" | grep -qE '^(fix|bugfix|hotfix|patch)\b'; then
    FIXED="${FIXED}- ${msg}
"
  elif echo "$lower" | grep -qE '^(remove|delete|deprecate|drop)\b'; then
    REMOVED="${REMOVED}- ${msg}
"
  else
    CHANGED="${CHANGED}- ${msg}
"
  fi
done < <(git log "$COMMIT_RANGE" --pretty=format:"%s" 2>/dev/null || true)

# Build the entry
ENTRY=""
ENTRY="${ENTRY}## [${VERSION}] - ${TODAY}
"

if [ -n "$ADDED" ]; then
  ENTRY="${ENTRY}
### Added
${ADDED}"
fi

if [ -n "$FIXED" ]; then
  ENTRY="${ENTRY}
### Fixed
${FIXED}"
fi

if [ -n "$CHANGED" ]; then
  ENTRY="${ENTRY}
### Changed
${CHANGED}"
fi

if [ -n "$REMOVED" ]; then
  ENTRY="${ENTRY}
### Removed
${REMOVED}"
fi

# Prepend to CHANGELOG.md or create it
if [ -f "$CHANGELOG_FILE" ]; then
  HEADER=""
  if head -1 "$CHANGELOG_FILE" | grep -q "^# Changelog"; then
    HEADER="# Changelog
"
  fi
  # Remove old header, prepend new entry after it
  TMP=$(mktemp)
  {
    echo "# Changelog"
    echo ""
    echo "$ENTRY"
    echo ""
    tail -n +2 "$CHANGELOG_FILE"
  } > "$TMP"
  mv "$TMP" "$CHANGELOG_FILE"
else
  {
    echo "# Changelog"
    echo ""
    echo "$ENTRY"
  } > "$CHANGELOG_FILE"
fi

echo "Changelog generated at ${CHANGELOG_FILE}"
