#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [since-tag] [output-file]

SINCE_TAG="${1:-}"
OUTPUT="${2:-CHANGELOG.md}"
DATE=$(date +"%Y-%m-%d")

# Find last tag if not specified
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE_TAG" ]]; then
  COMMITS=$(git log "${SINCE_TAG}..HEAD" --pretty=format:"%s" 2>/dev/null)
else
  COMMITS=$(git log --pretty=format:"%s" 2>/dev/null)
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found."
  exit 0
fi

ADDED="" FIXED="" CHANGED="" REMOVED="" OTHER=""

while IFS= read -r commit; do
  [[ -z "$commit" ]] && continue
  lower=$(echo "$commit" | tr '[:upper:]' '[:lower:]')
  msg="${commit#*: }"

  if echo "$lower" | grep -qE '^feat(\(.+\))?:'; then
    ADDED+="- $msg"$'\n'
  elif echo "$lower" | grep -qE '^fix(\(.+\))?:'; then
    FIXED+="- $msg"$'\n'
  elif echo "$lower" | grep -qE '^(refactor|perf|style|chore|docs|ci|build|test)(\(.+\))?:'; then
    CHANGED+="- $msg"$'\n'
  elif echo "$lower" | grep -qE '^(remove|delete|deprecat)'; then
    REMOVED+="- $commit"$'\n'
  elif echo "$lower" | grep -qE '^breaking'; then
    CHANGED+="- ⚠️ BREAKING: $msg"$'\n'
  else
    OTHER+="- $commit"$'\n'
  fi
done <<< "$COMMITS"

CURRENT_TAG=$(git describe --tags --exact-match HEAD 2>/dev/null || echo "Unreleased")

{
  echo "# Changelog"
  echo ""
  echo "## [$CURRENT_TAG] - $DATE"
  echo ""
  [[ -n "$ADDED" ]]   && echo "### Added"   && echo "$ADDED"
  [[ -n "$FIXED" ]]   && echo "### Fixed"   && echo "$FIXED"
  [[ -n "$CHANGED" ]] && echo "### Changed" && echo "$CHANGED"
  [[ -n "$REMOVED" ]] && echo "### Removed" && echo "$REMOVED"
  [[ -n "$OTHER" ]]   && echo "### Other"   && echo "$OTHER"
} > "$OUTPUT"

echo "✅ CHANGELOG written to $OUTPUT"
