#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
VERSION="${2:-Unreleased}"
TODAY="$(date -u +%Y-%m-%d)"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
else
  RANGE="HEAD"
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS="|" read -r hash subject; do
  [ -z "$hash" ] && continue
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  entry="- ${subject} (\`${hash}\`)"

  case "$lower" in
    feat*|add*|implement*)
      ADDED="${ADDED}${entry}"$'\n'
      ;;
    fix*|bugfix*|hotfix*|patch*|resolve*)
      FIXED="${FIXED}${entry}"$'\n'
      ;;
    remove*|delete*|drop*|deprecate*)
      REMOVED="${REMOVED}${entry}"$'\n'
      ;;
    *)
      CHANGED="${CHANGED}${entry}"$'\n'
      ;;
  esac
done < <(git log "$RANGE" --no-merges --pretty=format:"%h|%s")

{
  echo "# Changelog"
  echo ""
  echo "## [${VERSION}] - ${TODAY}"
  if [ -n "$LAST_TAG" ]; then
    echo "_Changes since tag \`${LAST_TAG}\`_"
  else
    echo "_Initial repository commit history_"
  fi
  echo ""

  if [ -n "$ADDED" ]; then
    echo "### Added"
    printf "%s\n" "$ADDED"
  fi
  if [ -n "$FIXED" ]; then
    echo "### Fixed"
    printf "%s\n" "$FIXED"
  fi
  if [ -n "$CHANGED" ]; then
    echo "### Changed"
    printf "%s\n" "$CHANGED"
  fi
  if [ -n "$REMOVED" ]; then
    echo "### Removed"
    printf "%s\n" "$REMOVED"
  fi
} > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE from range '$RANGE'."
