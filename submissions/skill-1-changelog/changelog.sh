#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>]

set -euo pipefail

OUTPUT="${CHANGELOG_OUTPUT:-CHANGELOG.md}"

# Determine start point: last tag, or first commit if no tags
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  SINCE="$LAST_TAG..HEAD"
else
  FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD)
  SINCE="$FIRST_COMMIT..HEAD"
fi

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## $(git tag --sort=-creatordate | head -1 || echo 'Unreleased') ($(date +%Y-%m-%d))" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Temporary files for categorization
ADDED=$(mktemp)
FIXED=$(mktemp)
CHANGED=$(mktemp)
REMOVED=$(mktemp)
OTHER=$(mktemp)

trap "rm -f $ADDED $FIXED $CHANGED $REMOVED $OTHER" EXIT

# Parse commits
git log "$SINCE" --pretty=format:"%s" | while IFS= read -r msg; do
  msg=$(echo "$msg" | sed 's/^ *//;s/ *$//')
  [ -z "$msg" ] && continue

  # Auto-categorize by prefix
  if echo "$msg" | grep -qiE '^(add|feat|new|introduce|create)'; then
    echo "- $msg" >> "$ADDED"
  elif echo "$msg" | grep -qiE '^(fix|bug|patch|resolve|hotfix|correct)'; then
    echo "- $msg" >> "$FIXED"
  elif echo "$msg" | grep -qiE '^(change|update|modify|refactor|improve|tweak|adjust)'; then
    echo "- $msg" >> "$CHANGED"
  elif echo "$msg" | grep -qiE '^(remove|delete|drop|deprecate|retire)'; then
    echo "- $msg" >> "$REMOVED"
  else
    echo "- $msg" >> "$OTHER"
  fi
done

# Output categorized sections
for CAT in "Added:$ADDED" "Fixed:$FIXED" "Changed:$CHANGED" "Removed:$REMOVED"; do
  LABEL="${CAT%%:*}"
  FILE="${CAT##*:}"
  if [ -s "$FILE" ]; then
    echo "### $LABEL" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    cat "$FILE" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi
done

# Other commits (uncategorized)
if [ -s "$OTHER" ]; then
  echo "### Other" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
  cat "$OTHER" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
fi

echo "Generated $OUTPUT ($(wc -l < "$OUTPUT") lines)"
echo "  Added:   $(wc -l < "$ADDED" 2>/dev/null || echo 0) commits"
echo "  Fixed:   $(wc -l < "$FIXED" 2>/dev/null || echo 0) commits"
echo "  Changed: $(wc -l < "$CHANGED" 2>/dev/null || echo 0) commits"
echo "  Removed: $(wc -l < "$REMOVED" 2>/dev/null || echo 0) commits"
