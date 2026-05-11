#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────
# generate-changelog.sh
# Generates a structured CHANGELOG.md from git history.
# Usage: bash generate-changelog.sh [--write]
# ──────────────────────────────────────────────────────────

WRITE=false
if [[ "${1:-}" == "--write" ]]; then
  WRITE=true
fi

# --- Find version source ---
# Use latest tag, or fall back to "0.1.0" + commit count
TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [[ -z "$TAG" ]]; then
  COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo "0")
  VERSION="0.1.0-dev.${COMMIT_COUNT}"
  TAG_RANGE="HEAD"
  SINCE_MSG="initial commit"
else
  VERSION="$TAG"
  SINCE_MSG="$TAG"
  # Get commits since the tag — exclude the tagged commit itself
  TAG_RANGE="${TAG}..HEAD"
fi

DATE=$(date +%Y-%m-%d)

# --- Get commit log ---
COMMITS=$(git log --oneline "$TAG_RANGE" 2>/dev/null || git log --oneline HEAD 2>/dev/null)

if [[ -z "$COMMITS" ]]; then
  echo "No new commits since ${SINCE_MSG}."
  exit 0
fi

# --- Default category keywords ---
ADDED_KEYWORDS="feat|feature|add|implement|create|new"
FIXED_KEYWORDS="fix|bug|hotfix|patch|correct|resolve"
CHANGED_KEYWORDS="refactor|chore|update|improve|perf|migrate|bump|upgrade"
REMOVED_KEYWORDS="remove|deprecate|delete|drop|deprecated"

# --- Categorize commits ---
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
UNCATEGORIZED=()

while IFS= read -r line; do
  # Remove leading hash + commit SHA (git log --oneline format: "abc123 message")
  msg="${line#* }"
  msg_lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if echo "$msg_lower" | grep -qE "^\s*(${ADDED_KEYWORDS})"; then
    ADDED+=("$msg")
  elif echo "$msg_lower" | grep -qE "^\s*(${FIXED_KEYWORDS})"; then
    FIXED+=("$msg")
  elif echo "$msg_lower" | grep -qE "^\s*(${CHANGED_KEYWORDS})"; then
    CHANGED+=("$msg")
  elif echo "$msg_lower" | grep -qE "^\s*(${REMOVED_KEYWORDS})"; then
    REMOVED+=("$msg")
  else
    UNCATEGORIZED+=("$msg")
  fi
done <<< "$COMMITS"

# --- Render changelog ---
render() {
  echo "# Changelog"
  echo ""
  echo "## [${VERSION}] - ${DATE}"
  echo ""

  [[ ${#ADDED[@]} -gt 0 ]]          && render_section "Added" "${ADDED[@]}"
  [[ ${#FIXED[@]} -gt 0 ]]          && render_section "Fixed" "${FIXED[@]}"
  [[ ${#CHANGED[@]} -gt 0 ]]        && render_section "Changed" "${CHANGED[@]}"
  [[ ${#REMOVED[@]} -gt 0 ]]        && render_section "Removed" "${REMOVED[@]}"
  [[ ${#UNCATEGORIZED[@]} -gt 0 ]]  && render_section "Uncategorized" "${UNCATEGORIZED[@]}"
}

render_section() {
  local heading="$1"
  shift
  local items=("$@")
  if [[ ${#items[@]} -gt 0 ]]; then
    echo "### ${heading}"
    for item in "${items[@]}"; do
      # Strip conventional commit prefix for clean output
      cleaned=$(echo "$item" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?:\s*//')
      echo "- ${cleaned}"
    done
    echo ""
  fi
}

if $WRITE; then
  render > CHANGELOG.md
  echo "Generated CHANGELOG.md"
else
  render
fi
