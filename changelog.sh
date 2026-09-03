#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-.}"
OUTPUT="${2:-CHANGELOG.md}"
cd "$REPO_DIR"

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
else
  RANGE="HEAD"
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  hash=$(echo "$line" | cut -d'|' -f1)
  msg=$(echo "$line" | cut -d'|' -f2-)
  short_hash="${hash:0:7}"

  case "$msg" in
    feat:*|feat\(*) ADDED="${ADDED}- ${msg#*: } (${short_hash})\n" ;;
    fix:*|fix\(*)   FIXED="${FIXED}- ${msg#*: } (${short_hash})\n" ;;
    refactor:*|perf:*|style:*) CHANGED="${CHANGED}- ${msg#*: } (${short_hash})\n" ;;
    revert:*|remove:*|delete:*) REMOVED="${REMOVED}- ${msg#*: } (${short_hash})\n" ;;
  esac
done < <(git log "$RANGE" --pretty=format:"%H|%s" 2>/dev/null || true)

{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased]"
  if [ -n "$ADDED" ]; then
    echo "### Added"
    printf "%b" "$ADDED"
  fi
  if [ -n "$FIXED" ]; then
    echo "### Fixed"
    printf "%b" "$FIXED"
  fi
  if [ -n "$CHANGED" ]; then
    echo "### Changed"
    printf "%b" "$CHANGED"
  fi
  if [ -n "$REMOVED" ]; then
    echo "### Removed"
    printf "%b" "$REMOVED"
  fi
} > "$OUTPUT"

echo "Generated $OUTPUT"
