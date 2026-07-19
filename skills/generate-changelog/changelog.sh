#!/usr/bin/env bash
set -euo pipefail

OUTPUT="CHANGELOG.md"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
  COMMITS=$(git log --pretty=format:"%s" --reverse)
else
  COMMITS=$(git log "$LAST_TAG..HEAD" --pretty=format:"%s" --reverse)
fi

cat > "$OUTPUT" << 'HEADER'
# Changelog

All notable changes to this project will be documented in this file.

HEADER

echo "## $(date +%Y-%m-%d)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

categorize() {
  local prefix="$1"
  local emoji="$2"
  local matches=$(echo "$COMMITS" | grep -i "^$prefix" || true)
  if [ -n "$matches" ]; then
    echo "### $emoji $prefix" >> "$OUTPUT"
    echo "$matches" | while IFS= read -r line; do
      clean="${line#*: }"
      [ -z "$clean" ] && clean="${line#$prefix}"
      echo "- ${clean:-$line}" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
  fi
}

categorize "Added" "✨"
categorize "Fixed" "🐛"
categorize "Changed" "🔧"
categorize "Removed" "🗑️"

echo "Generated $OUTPUT from $(echo "$COMMITS" | wc -l | tr -d ' ') commits."
