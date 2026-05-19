#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--from-tag TAG] [--output FILE]

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
FROM_TAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-tag)
      FROM_TAG="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# Determine the starting point
if [[ -n "$FROM_TAG" ]]; then
  RANGE="${FROM_TAG}..HEAD"
elif git tag --sort=-version:refname | head -1 | grep -q .; then
  LATEST_TAG=$(git tag --sort=-version:refname | head -1)
  RANGE="${LATEST_TAG}..HEAD"
else
  RANGE="HEAD"
fi

# Fetch commits with their subjects
COMMITS=$(git log "$RANGE" --pretty=format:"%h|%s" --no-merges 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range: $RANGE"
  exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS='|' read -r hash subject; do
  [[ -z "$hash" ]] && continue
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  if [[ "$lower" =~ ^(feat|feature|add)[:\ ] ]]; then
    ADDED="${ADDED}- ${subject} (${hash})\n"
  elif [[ "$lower" =~ ^(fix|bugfix|hotfix)[:\ ] ]]; then
    FIXED="${FIXED}- ${subject} (${hash})\n"
  elif [[ "$lower" =~ ^(remove|delete|deprecate)[:\ ] ]]; then
    REMOVED="${REMOVED}- ${subject} (${hash})\n"
  elif [[ "$lower" =~ ^(change|refactor|update|chore)[:\ ] ]]; then
    CHANGED="${CHANGED}- ${subject} (${hash})\n"
  else
    CHANGED="${CHANGED}- ${subject} (${hash})\n"
  fi
done <<< "$COMMITS"

# Determine version header
if [[ -n "$FROM_TAG" ]]; then
  HEADER="## [${FROM_TAG}] - $(date +%Y-%m-%d)"
elif git tag --sort=-version:refname | head -1 | grep -q .; then
  HEADER="## [Unreleased]"
else
  HEADER="## [Unreleased]"
fi

# Build the changelog
{
  echo "# Changelog"
  echo ""
  echo "$HEADER"
  echo ""

  if [[ -n "$ADDED" ]]; then
    echo "### Added"
    echo -e "$ADDED"
    echo ""
  fi

  if [[ -n "$FIXED" ]]; then
    echo "### Fixed"
    echo -e "$FIXED"
    echo ""
  fi

  if [[ -n "$CHANGED" ]]; then
    echo "### Changed"
    echo -e "$CHANGED"
    echo ""
  fi

  if [[ -n "$REMOVED" ]]; then
    echo "### Removed"
    echo -e "$REMOVED"
    echo ""
  fi
} > "$OUTPUT_FILE"

echo "✅ ${OUTPUT_FILE} generated successfully"
echo "   Commits processed: $(echo "$COMMITS" | wc -l | tr -d ' ')"
echo "   Range: $RANGE"
