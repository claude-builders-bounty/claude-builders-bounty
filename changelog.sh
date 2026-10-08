#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Claude Code Skill / CLI: Generate Structured CHANGELOG from Git History
# Categorizes commits into: Added, Fixed, Changed, Removed
# ==============================================================================

OUTPUT_FILE="CHANGELOG.md"
TARGET_DIR="${1:-.}"

cd "$TARGET_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Directory '$TARGET_DIR' is not a git repository." >&2
  exit 1
fi

# Detect the most recent tag
LAST_TAG=""
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG=$(git describe --tags --abbrev=0)
  REVISION_RANGE="${LAST_TAG}..HEAD"
  HEADER_VERSION="Unreleased (since ${LAST_TAG})"
else
  REVISION_RANGE="HEAD"
  HEADER_VERSION="Initial Release"
fi

TODAY=$(date +'%Y-%m-%d')

# Temporary storage for categorized entries
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ADDED_FILE="$TMP_DIR/added.txt"
FIXED_FILE="$TMP_DIR/fixed.txt"
CHANGED_FILE="$TMP_DIR/changed.txt"
REMOVED_FILE="$TMP_DIR/removed.txt"
OTHER_FILE="$TMP_DIR/other.txt"

touch "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE" "$OTHER_FILE"

# Extract commits: hash|subject
git log "$REVISION_RANGE" --no-merges --format="%h|%s" | while IFS='|' read -r HASH SUBJECT; do
  [ -z "$HASH" ] && continue

  LOWER_SUBJ=$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')

  # Determine category based on Conventional Commits & keywords
  if [[ "$LOWER_SUBJ" =~ ^feat(\(.*\))?:|^add(\(.*\))?:|add\ |added\ |new\ |feature ]]; then
    CLEAN_MSG=$(echo "$SUBJECT" | sed -E 's/^(feat|add)(\([^)]+\))?:\s*//I')
    echo "- ${CLEAN_MSG} (\`${HASH}\`)" >> "$ADDED_FILE"
  elif [[ "$LOWER_SUBJ" =~ ^fix(\(.*\))?:|^bug(\(.*\))?:|fix\ |fixed\ |patch ]]; then
    CLEAN_MSG=$(echo "$SUBJECT" | sed -E 's/^(fix|bug)(\([^)]+\))?:\s*//I')
    echo "- ${CLEAN_MSG} (\`${HASH}\`)" >> "$FIXED_FILE"
  elif [[ "$LOWER_SUBJ" =~ ^remove(\(.*\))?:|^delete(\(.*\))?:|remove\ |removed\ |delete\ |deprecated ]]; then
    CLEAN_MSG=$(echo "$SUBJECT" | sed -E 's/^(remove|delete)(\([^)]+\))?:\s*//I')
    echo "- ${CLEAN_MSG} (\`${HASH}\`)" >> "$REMOVED_FILE"
  elif [[ "$LOWER_SUBJ" =~ ^refactor(\(.*\))?:|^perf(\(.*\))?:|^style(\(.*\))?:|^chore(\(.*\))?:|^change(\(.*\))?:|update|refactor|change ]]; then
    CLEAN_MSG=$(echo "$SUBJECT" | sed -E 's/^(refactor|perf|style|chore|change)(\([^)]+\))?:\s*//I')
    echo "- ${CLEAN_MSG} (\`${HASH}\`)" >> "$CHANGED_FILE"
  else
    echo "- ${SUBJECT} (\`${HASH}\`)" >> "$CHANGED_FILE"
  fi
done

# Assemble CHANGELOG
NEW_SECTION="$TMP_DIR/new_section.md"
{
  echo "## [${HEADER_VERSION}] - ${TODAY}"
  echo ""
  
  if [ -s "$ADDED_FILE" ]; then
    echo "### Added"
    cat "$ADDED_FILE"
    echo ""
  fi

  if [ -s "$FIXED_FILE" ]; then
    echo "### Fixed"
    cat "$FIXED_FILE"
    echo ""
  fi

  if [ -s "$CHANGED_FILE" ]; then
    echo "### Changed"
    cat "$CHANGED_FILE"
    echo ""
  fi

  if [ -s "$REMOVED_FILE" ]; then
    echo "### Removed"
    cat "$REMOVED_FILE"
    echo ""
  fi
} > "$NEW_SECTION"

# Write or prepend to CHANGELOG.md
if [ -f "$OUTPUT_FILE" ]; then
  # If file already exists and has a main heading, insert below heading
  if grep -q "^# Changelog" "$OUTPUT_FILE" || grep -q "^# CHANGELOG" "$OUTPUT_FILE"; then
    TMP_OUT="$TMP_DIR/final_changelog.md"
    awk -v sec="$(cat "$NEW_SECTION")" '
      NR==1 { print; print ""; print sec; next }
      { print }
    ' "$OUTPUT_FILE" > "$TMP_OUT"
    mv "$TMP_OUT" "$OUTPUT_FILE"
  else
    cat "$NEW_SECTION" "$OUTPUT_FILE" > "$OUTPUT_FILE.tmp"
    mv "$OUTPUT_FILE.tmp" "$OUTPUT_FILE"
  fi
else
  {
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)."
    echo ""
    cat "$NEW_SECTION"
  } > "$OUTPUT_FILE"
fi

echo "✅ Generated $OUTPUT_FILE successfully for range: $REVISION_RANGE"
