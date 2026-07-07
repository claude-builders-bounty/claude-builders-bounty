#!/bin/bash
# Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output-file]
# Works as: /generate-changelog in Claude Code
set -e

OUTPUT="${1:-CHANGELOG.md}"

# Initialize the changelog file
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
} > "$OUTPUT"

# Get the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
  SCOPE=""
  VERSION="unreleased"
else
  SCOPE="${LAST_TAG}..HEAD"
  VERSION=$(git describe --tags 2>/dev/null || echo "v0.1.0")
fi

echo "## [${VERSION}] - $(date +%Y-%m-%d)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Collect commits by category
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS= read -r line; do
  [ -z "$line" ] && continue
  msg="${line}"
  if echo "$msg" | grep -qiE '^(feat|add|new|create|implement|introduce)\b'; then
    ADDED+=("$msg")
  elif echo "$msg" | grep -qiE '^(fix|bug|hotfix|patch|correct|resolve|repair)\b'; then
    FIXED+=("$msg")
  elif echo "$msg" | grep -qiE '^(remove|delete|drop|deprecate|revert|chore)\b'; then
    REMOVED+=("$msg")
  else
    CHANGED+=("$msg")
  fi
done < <(git log $SCOPE --reverse --pretty=format:"%s" --no-merges 2>/dev/null || echo "")

write_category() {
  local label="$1"
  shift
  local items=("$@")
  if [ ${#items[@]} -gt 0 ]; then
    echo "### ${label}" >> "$OUTPUT"
    for item in "${items[@]}"; do
      echo "- ${item}" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
  fi
}

write_category "Added" "${ADDED[@]}"
write_category "Fixed" "${FIXED[@]}"
write_category "Changed" "${CHANGED[@]}"
write_category "Removed" "${REMOVED[@]}"

echo "✅ CHANGELOG.md generated at ${OUTPUT}"
