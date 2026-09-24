#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   cd /path/to/your/repo
#   bash changelog.sh
#
# The script:
# 1. Finds the last tag (or falls back to the initial commit)
# 2. Fetches all commits since that tag
# 3. Auto-categorizes into: Added / Fixed / Changed / Removed
# 4. Outputs CHANGELOG.md with today's date and version
# 5. Prepends to CHANGELOG.md (creates it if missing)
#
# Requirements: git, bash

set -euo pipefail

# --- Config ---
OUTPUT_FILE="CHANGELOG.md"
DATE=$(date +%Y-%m-%d)

# Find the last tag (most recent, sorted by version)
LAST_TAG=$(git tag --sort=-version:refname | head -1)

# Determine version and range
if [ -z "$LAST_TAG" ]; then
  VERSION="0.1.0"
  RANGE="HEAD"
  echo "No tags found. Generating changelog from all commits." >&2
else
  # Bump patch version
  VERSION=$(echo "$LAST_TAG" | sed 's/^v//' | awk -F. '{print $1"."$2"."$3+1}')
  RANGE="${LAST_TAG}..HEAD"
fi

# --- Categorize commits by conventional commit prefix ---
ALL_SUBJECTS=$(git log "$RANGE" --format="%s" 2>/dev/null || true)

ADDED=$(echo "$ALL_SUBJECTS" | grep -iE '^(feat|feature|add)\b' || true)
FIXED=$(echo "$ALL_SUBJECTS" | grep -iE '^(fix|bug|hotfix)\b' || true)
CHANGED=$(echo "$ALL_SUBJECTS" | grep -iE '^(refactor|update|perf|style|chore|docs|test|ci|build)\b' || true)
REMOVED=$(echo "$ALL_SUBJECTS" | grep -iE '^(remove|deprecate|delete)\b' || true)

# --- Build changelog entry via temp file ---
TEMP_ENTRY=$(mktemp)

echo "## [$VERSION] - $DATE" >> "$TEMP_ENTRY"
echo "" >> "$TEMP_ENTRY"

# Append a section to the temp file
append_section() {
  local label="$1"
  local commits="$2"
  if [ -n "$commits" ]; then
    echo "### $label" >> "$TEMP_ENTRY"
    echo "" >> "$TEMP_ENTRY"
    echo "$commits" | while IFS= read -r line; do
      echo "- $line" >> "$TEMP_ENTRY"
    done
    echo "" >> "$TEMP_ENTRY"
  fi
}

append_section "Added" "$ADDED"
append_section "Fixed" "$FIXED"
append_section "Changed" "$CHANGED"
append_section "Removed" "$REMOVED"

# If no categorized commits, include raw log
if [ -z "$ADDED$FIXED$CHANGED$REMOVED" ]; then
  echo "### Added" >> "$TEMP_ENTRY"
  echo "" >> "$TEMP_ENTRY"
  echo "$ALL_SUBJECTS" | head -20 | while IFS= read -r line; do
    echo "- $line" >> "$TEMP_ENTRY"
  done
  echo "" >> "$TEMP_ENTRY"
fi

# --- Write to file ---
if [ -f "$OUTPUT_FILE" ]; then
  # Prepend to existing CHANGELOG
  TEMP=$(mktemp)
  cat "$TEMP_ENTRY" > "$TEMP"
  cat "$OUTPUT_FILE" >> "$TEMP"
  mv "$TEMP" "$OUTPUT_FILE"
else
  # Create new CHANGELOG
  echo "# Changelog" > "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  cat "$TEMP_ENTRY" >> "$OUTPUT_FILE"
fi

rm -f "$TEMP_ENTRY"

echo "✅ Generated $OUTPUT_FILE (version ${VERSION})"

# Show preview
echo ""
echo "--- Preview ---"
head -20 "$OUTPUT_FILE"