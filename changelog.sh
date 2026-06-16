#!/bin/bash
# changelog.sh - Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [tag]
# If no tag given, uses commits since last tag (or all commits if no tags)

set -euo pipefail

TARGET_TAG="${1:-}"

if [ -z "$TARGET_TAG" ]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [ -n "$LAST_TAG" ]; then
    RANGE="$LAST_TAG..HEAD"
  else
    RANGE="HEAD"
  fi
else
  RANGE="$TARGET_TAG"
fi

echo "Generating CHANGELOG from range: $RANGE"

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  msg=$(echo "$line" | sed 's/^[a-f0-9]* //')
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  case "$lower" in
    feat*|add*|new*|implement*|introduce*)
      ADDED="$ADDED
- $msg"
      ;;
    fix*|bug*|patch*|resolve*|correct*)
      FIXED="$FIXED
- $msg"
      ;;
    remove*|delete*|drop*|deprecat*)
      REMOVED="$REMOVED
- $msg"
      ;;
    *)
      CHANGED="$CHANGED
- $msg"
      ;;
  esac
done < <(git log --oneline $RANGE 2>/dev/null)

DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --always 2>/dev/null || echo "unreleased")

{
  echo "# Changelog"
  echo ""
  echo "## [$VERSION] - $DATE"
  echo ""

  if [ -n "$ADDED" ]; then
    echo "### Added"
    echo "$ADDED"
    echo ""
  fi

  if [ -n "$FIXED" ]; then
    echo "### Fixed"
    echo "$FIXED"
    echo ""
  fi

  if [ -n "$CHANGED" ]; then
    echo "### Changed"
    echo "$CHANGED"
    echo ""
  fi

  if [ -n "$REMOVED" ]; then
    echo "### Removed"
    echo "$REMOVED"
    echo ""
  fi
} > CHANGELOG.md

echo "✅ CHANGELOG.md generated successfully"
echo "   Version: $VERSION"
echo "   Date: $DATE"
