#!/bin/bash
set -euo pipefail

# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--output CHANGELOG.md]

OUTPUT="${2:-CHANGELOG.md}"
REPO_DIR="$PWD"

# Get the last tag (fallback to first commit if no tags)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "All notable changes to this project will be documented in this file." >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Helper to extract conventional commit types
generate_section() {
  local TAG="$1"
  local TYPE="$2"
  local EMOJI="$3"
  local HEADING="$4"

  local COMMITS
  COMMITS=$(git log "$TAG"..HEAD --pretty=format:"%s" --grep="^$TYPE" 2>/dev/null || true)

  if [ -n "$COMMITS" ]; then
    echo "### $HEADING" >> "$OUTPUT"
    echo "$COMMITS" | while IFS= read -r line; do
      local CLEAN="${line#*: }"
      echo "- $CLEAN" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
  fi
}

generate_section "HEAD" "feat" "✨" "Added"
generate_section "HEAD" "fix" "🐛" "Fixed"
generate_section "HEAD" "refactor" "♻️" "Changed"
generate_section "HEAD" "chore" "🔧" "Changed"
generate_section "HEAD" "style" "💄" "Changed"
generate_section "HEAD" "perf" "⚡" "Changed"
generate_section "HEAD" "docs" "📝" "Changed"

# Check for breaking changes
BREAKING=$(git log HEAD..HEAD --pretty=format:"%s" --grep="BREAKING" 2>/dev/null || true)
if [ -n "$BREAKING" ]; then
  echo "### ⚠️ Removed / Breaking" >> "$OUTPUT"
  echo "$BREAKING" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
fi

echo "Generated CHANGELOG at $OUTPUT"
echo "---"
head -20 "$OUTPUT"
