#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
TODAY=$(date +%Y-%m-%d)

# Get last tag or fall back to initial commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
else
  RANGE="HEAD"
fi

declare -A CATEGORIES
CATEGORIES=( ["added"]="" ["fixed"]="" ["changed"]="" ["removed"]="" )

while IFS= read -r line; do
  hash=$(echo "$line" | cut -d'|' -f1)
  msg=$(echo "$line" | cut -d'|' -f2-)
  short_hash="${hash:0:7}"

  # Strip leading type(scope): prefix for display
  display_msg=$(echo "$msg" | sed -E 's/^(feat|fix|refactor|style|perf|revert|remove|delete|chore|docs|test|ci|build)(\(.+\))?:\s*//')

  entry="- ${display_msg} (${short_hash})"

  case "$msg" in
    feat:*|feat\(*) CATEGORIES["added"]+="${entry}\n" ;;
    fix:*|fix\(*)   CATEGORIES["fixed"]+="${entry}\n" ;;
    revert:*|revert\(*|remove:*|remove\(*|delete:*|delete\(*) CATEGORIES["removed"]+="${entry}\n" ;;
    *)              CATEGORIES["changed"]+="${entry}\n" ;;
  esac
done < <(git log "$RANGE" --pretty=format:"%H|%s" --reverse)

{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased] - ${TODAY}"
  echo ""

  for category in added fixed changed removed; do
    items="${CATEGORIES[$category]}"
    if [ -n "$items" ]; then
      title="$(echo "$category" | sed 's/^./\U&/')"
      echo "### ${title}"
      echo -e "$items"
    fi
  done
} > "$OUTPUT"

echo "✅ Generated ${OUTPUT}"
