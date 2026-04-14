#!/bin/bash
#
# changelog.sh — Generate CHANGELOG.md from git history since last tag
#
# Usage:
#   ./changelog.sh                     # print to stdout
#   ./changelog.sh -o CHANGELOG.md     # write to file
#   ./changelog.sh --from v1.0.0       # use specific starting tag
#
set -euo pipefail

FROM_TAG=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output) OUTPUT_FILE="$2"; shift 2 ;;
    --from) FROM_TAG="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Determine the range of commits
LAST_TAG=""
if [[ -n "$FROM_TAG" ]]; then
  RANGE="${FROM_TAG}..HEAD"
else
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$LAST_TAG" ]]; then
    RANGE="${LAST_TAG}..HEAD"
  else
    RANGE=""
  fi
fi

TODAY=$(date +%Y-%m-%d)
NEXT_VERSION="${LAST_TAG:-v0.0.1}"

# Collect all commit lines
COMMITS_FILE=$(mktemp)
trap 'rm -f "$COMMITS_FILE"' EXIT

if [[ -n "$RANGE" ]]; then
  git log "${RANGE}" --pretty=format:"%s" > "$COMMITS_FILE" 2>/dev/null || true
else
  git log --pretty=format:"%s" > "$COMMITS_FILE" 2>/dev/null || true
fi

# Build the changelog content
build_changelog() {
  echo "# Changelog"
  echo ""
  echo "## ${NEXT_VERSION} (${TODAY})"
  echo ""

  local PATTERN_ADDED="^(add|feat|new|implement|create|introduce)"
  local PATTERN_FIXED="^(fix|bug|patch|resolve|hotfix)"
  local PATTERN_CHANGED="^(change|update|modify|refactor|improve|optimize|rename)"
  local PATTERN_REMOVED="^(remove|delete|deprecate|drop|clean)"

  local ALL_PATTERNS="${PATTERN_ADDED}|${PATTERN_FIXED}|${PATTERN_CHANGED}|${PATTERN_REMOVED}"

  emit_category() {
    local label="$1"
    local pattern="$2"
    local matches
    matches=$(grep -iE "${pattern}" "$COMMITS_FILE" 2>/dev/null || true)
    if [[ -n "$matches" ]]; then
      echo "### ${label}"
      echo ""
      while IFS= read -r line; do
        local cleaned
        cleaned=$(echo "$line" | sed -E 's/\s*\(#([0-9]+)\)$//')
        echo "- ${cleaned}"
      done <<< "$matches"
      echo ""
    fi
  }

  emit_category "Added" "${PATTERN_ADDED}"
  emit_category "Fixed" "${PATTERN_FIXED}"
  emit_category "Changed" "${PATTERN_CHANGED}"
  emit_category "Removed" "${PATTERN_REMOVED}"

  # Uncategorized commits
  local UNCAT=0
  while IFS= read -r line; do
    if ! echo "$line" | grep -iqE "${ALL_PATTERNS}"; then
      UNCAT=$((UNCAT + 1))
    fi
  done < "$COMMITS_FILE"

  if [[ "$UNCAT" -gt 0 ]]; then
    echo "### Other"
    echo ""
    while IFS= read -r line; do
      if ! echo "$line" | grep -iqE "${ALL_PATTERNS}"; then
        local cleaned
        cleaned=$(echo "$line" | sed -E 's/\s*\(#([0-9]+)\)$//')
        echo "- ${cleaned}"
      fi
    done < "$COMMITS_FILE"
    echo ""
  fi
}

# Output
if [[ -n "$OUTPUT_FILE" ]]; then
  build_changelog > "$OUTPUT_FILE"
  echo "✅ CHANGELOG generated → ${OUTPUT_FILE}"
else
  build_changelog
fi
