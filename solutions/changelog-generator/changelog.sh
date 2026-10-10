#!/usr/bin/env bash
# ==============================================================================
# Git Changelog Generator
# Generates a structured CHANGELOG.md categorized by Conventional Commits
# Categories: Added, Fixed, Changed, Removed
# Format: Keep a Changelog (https://keepachangelog.com/en/1.0.0/)
# ==============================================================================

set -euo pipefail

TARGET_FILE="${1:-CHANGELOG.md}"
CUSTOM_RANGE="${2:-}"

# 1. Verify inside a git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Not inside a valid git repository." >&2
  exit 1
fi

# 2. Check if repository has any commits
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "Warning: Repository has no commits yet." >&2
  exit 0
fi

# 3. Determine commit range
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$CUSTOM_RANGE" ]; then
  COMMIT_RANGE="$CUSTOM_RANGE"
  VERSION_HEADER="Range: ${CUSTOM_RANGE}"
elif [ -n "$LAST_TAG" ]; then
  COMMIT_RANGE="${LAST_TAG}..HEAD"
  VERSION_HEADER="Changes since ${LAST_TAG}"
else
  COMMIT_RANGE="HEAD"
  VERSION_HEADER="Unreleased / Initial Release"
fi

echo "Analyzing git commits in range: ${COMMIT_RANGE}..."

# 4. Extract commits using unit separator (0x1f) to prevent delimiter collision
TMP_LOG=$(mktemp)
trap 'rm -f "$TMP_LOG"' EXIT

git log "${COMMIT_RANGE}" --pretty=format:'%h%x1f%s%x1f%an%x1f%ad' --date=short > "$TMP_LOG" || {
  echo "Error: Failed to read git log for range ${COMMIT_RANGE}." >&2
  exit 1
}

declare -a ADDED_LIST=()
declare -a FIXED_LIST=()
declare -a CHANGED_LIST=()
declare -a REMOVED_LIST=()

# Categorization patterns: Supports Conventional Commits & Natural Imperative English
REG_ADDED="^(feat(\([^\)]*\))?!?:|add(\([^\)]*\))?!?:|added:|new:|^add |^added |^create |^implement )"
REG_FIXED="^(fix(\([^\)]*\))?!?:|bugfix(\([^\)]*\))?!?:|fixed:|patch:|security:|^fix |^fixed |^resolve |^resolved )"
REG_REMOVED="^(remove(\([^\)]*\))?!?:|revert(\([^\)]*\))?!?:|removed:|deprecate:|deprecated:|^remove |^removed |^delete |^deleted |^revert )"
REG_CHANGED="^(refactor(\([^\)]*\))?!?:|perf(\([^\)]*\))?!?:|change:|chore(\([^\)]*\))?!?:|style(\([^\)]*\))?!?:|docs(\([^\)]*\))?!?:|build(\([^\)]*\))?!?:|ci(\([^\)]*\))?!?:|test(\([^\)]*\))?!?:|^update |^updated |^change |^refactor |^upgrade )"

TOTAL_COMMITS=0

while IFS=$'\x1f' read -r commit_hash commit_msg author commit_date || [ -n "${commit_hash:-}" ]; do
  [ -z "$commit_hash" ] && continue
  TOTAL_COMMITS=$((TOTAL_COMMITS + 1))

  # Sanitize commit message to avoid raw markdown injection issues
  clean_msg=$(echo "$commit_msg" | tr '\r\n' '  ')
  entry="- ${clean_msg} (\`${commit_hash}\`) - *${author}*, ${commit_date}"
  lower_msg=$(echo "$clean_msg" | tr '[:upper:]' '[:lower:]')

  if [[ "$lower_msg" =~ $REG_ADDED ]]; then
    ADDED_LIST+=("$entry")
  elif [[ "$lower_msg" =~ $REG_FIXED ]]; then
    FIXED_LIST+=("$entry")
  elif [[ "$lower_msg" =~ $REG_REMOVED ]]; then
    REMOVED_LIST+=("$entry")
  elif [[ "$lower_msg" =~ $REG_CHANGED ]]; then
    CHANGED_LIST+=("$entry")
  else
    # Default uncategorized commits to Changed under standard Keep a Changelog
    CHANGED_LIST+=("$entry")
  fi
done < "$TMP_LOG"

TODAY=$(date +%Y-%m-%d)

# 5. Render Keep a Changelog Markdown
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)."
  echo ""
  echo "## [${VERSION_HEADER}] - ${TODAY}"
  echo ""
  if [ "$TOTAL_COMMITS" -eq 0 ]; then
    echo "*No changes found in range ${COMMIT_RANGE}.*"
    echo ""
  else
    if [ ${#ADDED_LIST[@]} -gt 0 ]; then
      echo "### Added"
      printf '%s\n' "${ADDED_LIST[@]}"
      echo ""
    fi
    if [ ${#FIXED_LIST[@]} -gt 0 ]; then
      echo "### Fixed"
      printf '%s\n' "${FIXED_LIST[@]}"
      echo ""
    fi
    if [ ${#CHANGED_LIST[@]} -gt 0 ]; then
      echo "### Changed"
      printf '%s\n' "${CHANGED_LIST[@]}"
      echo ""
    fi
    if [ ${#REMOVED_LIST[@]} -gt 0 ]; then
      echo "### Removed"
      printf '%s\n' "${REMOVED_LIST[@]}"
      echo ""
    fi
  fi
} > "$TARGET_FILE"

echo "Changelog successfully generated: ${TARGET_FILE} (${TOTAL_COMMITS} commits processed)"
