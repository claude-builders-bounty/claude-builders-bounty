#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Part of the changelog-generator skill
# Usage: bash changelog.sh [output-file]
#   output-file defaults to CHANGELOG.md in the current directory
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

# Validate we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "⚠️  Not a git repository. Run this command inside a git project."
  exit 1
fi

# Find last tag, or fall back to initial commit
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -z "$LAST_TAG" ]; then
  FIRST_COMMIT="$(git log --oneline --reverse --format="%H" 2>/dev/null | head -1)"
  if [ -z "$FIRST_COMMIT" ]; then
    echo "⚠️  No commits found in this repository."
    exit 1
  fi
  RANGE="${FIRST_COMMIT}..HEAD"
  echo "📋 No tags found. Using full commit history (from initial commit)."
else
  RANGE="${LAST_TAG}..HEAD"
  echo "📋 Generating changelog since tag: ${LAST_TAG}"
fi

# Check if there are any new commits
COMMIT_COUNT="$(git log "${RANGE}" --oneline --no-merges 2>/dev/null | wc -l | tr -d ' ')"
if [ "$COMMIT_COUNT" -eq 0 ]; then
  echo "📭 No new commits since last tag. Nothing to add."
  exit 0
fi

echo "📦 Found ${COMMIT_COUNT} commit(s) to process."

# --- Categorize commits ---
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

# Read all commit messages and hashes
while IFS='|' read -r HASH SUBJECT; do
  # Determine category from conventional commit prefix
  CATEGORY="other"
  case "$SUBJECT" in
    feat:*|feature:*|add:*|implement:*|create:*|introduce:*)
      CATEGORY="added" ;;
    fix:*|bug:*|correct:*|hotfix:*|patch:*|resolve:*)
      CATEGORY="fixed" ;;
    refactor:*|perf:*|style:*|update:*|improve:*|migrate:*|redesign:*|rework:*)
      CATEGORY="changed" ;;
    remove:*|delete:*|deprecate:*|drop:*|cleanup:*|purge:*)
      CATEGORY="removed" ;;
    docs:*|test:*|chore:*|ci:*|build:*|wip:*)
      CATEGORY="other" ;;
    *)
      # Heuristic: look for keywords in the subject
      lower_subject="$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')"
      case "$lower_subject" in
        *"add"*|*"new"*|*"implement"*|*"create"*|*"introduce"*|*"support"*)
          CATEGORY="added" ;;
        *"fix"*|*"bug"*|*"correct"*|*"patch"*|*"resolve"*|*"hotfix"*)
          CATEGORY="fixed" ;;
        *"remove"*|*"delete"*|*"drop"*|*"deprecate"*|*"cleanup"*)
          CATEGORY="removed" ;;
        *"refactor"*|*"update"*|*"improve"*|*"migrate"*|*"redesign"*|*"change"*)
          CATEGORY="changed" ;;
      esac
      ;;
  esac

  ENTRY="- ${SUBJECT} (${HASH})"

  case "$CATEGORY" in
    added)   ADDED+=("$ENTRY") ;;
    fixed)   FIXED+=("$ENTRY") ;;
    changed) CHANGED+=("$ENTRY") ;;
    removed) REMOVED+=("$ENTRY") ;;
    other)   # Skip for clean output
      ;;
  esac
done < <(git log "${RANGE}" --no-merges --format="%h|%s" 2>/dev/null)

# --- Build the changelog ---
if [ -f "$OUTPUT" ] && grep -q "^## \[Unreleased\]" "$OUTPUT" 2>/dev/null; then
  # Extract everything after the Unreleased section (released version history)
  # Strategy: regenerate the header + new entries, then append old released versions
  TEMP_FILE="$(mktemp)"
  cat > "$TEMP_FILE" << 'HEADER'
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

HEADER

  # Find the line number of the first version header AFTER Unreleased
  FIRST_VERSION_LINE=$(grep -n "^## \[" "$OUTPUT" | tail -n +2 | head -1 | cut -d: -f1)

  # Write new sections
  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added" >> "$TEMP_FILE"
    for entry in "${ADDED[@]}"; do echo "$entry" >> "$TEMP_FILE"; done
    echo "" >> "$TEMP_FILE"
  fi

  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed" >> "$TEMP_FILE"
    for entry in "${FIXED[@]}"; do echo "$entry" >> "$TEMP_FILE"; done
    echo "" >> "$TEMP_FILE"
  fi

  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed" >> "$TEMP_FILE"
    for entry in "${CHANGED[@]}"; do echo "$entry" >> "$TEMP_FILE"; done
    echo "" >> "$TEMP_FILE"
  fi

  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed" >> "$TEMP_FILE"
    for entry in "${REMOVED[@]}"; do echo "$entry" >> "$TEMP_FILE"; done
    echo "" >> "$TEMP_FILE"
  fi

  # Append old released versions if they exist
  if [ -n "$FIRST_VERSION_LINE" ]; then
    tail -n +"$FIRST_VERSION_LINE" "$OUTPUT" >> "$TEMP_FILE"
  fi

  mv "$TEMP_FILE" "$OUTPUT"
else
  # Create new CHANGELOG.md
  cat > "$OUTPUT" << 'HEADER'
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

HEADER

  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added" >> "$OUTPUT"
    for entry in "${ADDED[@]}"; do echo "$entry" >> "$OUTPUT"; done
    echo "" >> "$OUTPUT"
  fi

  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed" >> "$OUTPUT"
    for entry in "${FIXED[@]}"; do echo "$entry" >> "$OUTPUT"; done
    echo "" >> "$OUTPUT"
  fi

  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed" >> "$OUTPUT"
    for entry in "${CHANGED[@]}"; do echo "$entry" >> "$OUTPUT"; done
    echo "" >> "$OUTPUT"
  fi

  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed" >> "$OUTPUT"
    for entry in "${REMOVED[@]}"; do echo "$entry" >> "$OUTPUT"; done
    echo "" >> "$OUTPUT"
  fi

  echo "" >> "$OUTPUT"
fi

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))
echo "✅ ${OUTPUT} updated with ${TOTAL} categorized changes."
