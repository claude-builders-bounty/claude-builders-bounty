#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Zero dependencies. POSIX-compatible. Under 50 lines of logic.
set -euo pipefail

OUTFILE="${1:-CHANGELOG.md}"
DATE=$(date +%Y-%m-%d)

# Determine range: last tag → HEAD, or all commits if untagged
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  HEADER="## [$DATE] — Changes since $LAST_TAG"
else
  RANGE="HEAD"
  HEADER="## [$DATE] — Full History"
fi

# Collect non-merge commits as "short_hash|subject"
COMMITS=$(git log "$RANGE" --no-merges --pretty=format:"%h|%s" 2>/dev/null || true)
if [ -z "$COMMITS" ]; then
  echo "No new commits found since ${LAST_TAG:-repository inception}. Nothing to generate."
  exit 0
fi

# Categorize each commit by conventional-commit prefix
ADDED="" FIXED="" CHANGED="" REMOVED=""
while IFS='|' read -r hash subject; do
  entry="- ${subject} (\`${hash}\`)"
  # Lowercase the subject for matching, keep original for display
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    feat:*|feat\(*|add:*|new:*)        ADDED="${ADDED}\n${entry}" ;;
    fix:*|fix\(*|bug:*|patch:*)        FIXED="${FIXED}\n${entry}" ;;
    remove:*|delete:*|revert:*)        REMOVED="${REMOVED}\n${entry}" ;;
    *)                                 CHANGED="${CHANGED}\n${entry}" ;;
  esac
done <<< "$COMMITS"

# Build the changelog content
{
  echo "# Changelog"
  echo ""
  echo "$HEADER"
  echo ""
  [ -n "$ADDED" ]   && printf "### Added\n%b\n\n" "$ADDED"
  [ -n "$FIXED" ]   && printf "### Fixed\n%b\n\n" "$FIXED"
  [ -n "$CHANGED" ] && printf "### Changed\n%b\n\n" "$CHANGED"
  [ -n "$REMOVED" ] && printf "### Removed\n%b\n\n" "$REMOVED"
} > "$OUTFILE"

echo "✅ Generated ${OUTFILE} ($(grep -c '^\-' "$OUTFILE") entries)"
