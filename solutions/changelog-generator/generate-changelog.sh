#!/usr/bin/env bash
# generate-changelog.sh — Auto-generate CHANGELOG.md from git history
# Usage: bash changelog_gen.sh [output_file]

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo '')"

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"

if [ -z "$LAST_TAG" ]; then
  echo "## [Unreleased]" >> "$OUTPUT"
  RANGE="HEAD"
else
  echo "## [Unreleased] (since $LAST_TAG)" >> "$OUTPUT"
  RANGE="${LAST_TAG}..HEAD"
fi
echo "" >> "$OUTPUT"

# Get all commits in range
ALL_COMMITS=$(git log "$RANGE" --oneline 2>/dev/null || true)

if [ -z "$ALL_COMMITS" ]; then
  echo "_No changes since last release._" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
  echo "✅ Generated $OUTPUT" >&2
  cat "$OUTPUT"
  exit 0
fi

# Categorize by commit message prefix
ADDED=$(echo "$ALL_COMMITS" | grep -iE '^(feat|add|new|implement|create)' || true)
FIXED=$(echo "$ALL_COMMITS" | grep -iE '^(fix|bug|patch|correct|hotfix)' || true)
CHANGED=$(echo "$ALL_COMMITS" | grep -iE '^(refactor|perf|update|improve|migrate|chore|docs|style|test)' || true)
REMOVED=$(echo "$ALL_COMMITS" | grep -iE '^(revert|remove|delete|deprecate|drop)' || true)

_write_section() {
  local label="$1" content="$2"
  if [ -n "$content" ]; then
    echo "### $label" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    while IFS= read -r line; do
      if [ -n "$line" ]; then
        hash=$(echo "$line" | awk '{print $1}')
        msg=$(echo "$line" | cut -d' ' -f2-)
        echo "- $msg (\`$hash\`)" >> "$OUTPUT"
      fi
    done <<< "$content"
    echo "" >> "$OUTPUT"
  fi
}

_write_section "Added" "$ADDED"
_write_section "Fixed" "$FIXED"
_write_section "Changed" "$CHANGED"
_write_section "Removed" "$REMOVED"

# Catch any uncategorized commits
CATEGORIZED=$(echo "$ADDED$FIXED$CHANGED$REMOVED" | grep -c . || true)
TOTAL=$(echo "$ALL_COMMITS" | wc -l)
UNCAT=$(echo "$ALL_COMMITS" | grep -v -iE '^(feat|fix|refactor|perf|chore|docs|style|test|revert|remove|delete|deprecate|drop|add|new|implement|create|update|improve|migrate|bug|patch|correct|hotfix)' || true)
if [ -n "$UNCAT" ]; then
  _write_section "Other" "$UNCAT"
fi

echo "✅ Generated $OUTPUT" >&2
cat "$OUTPUT"
