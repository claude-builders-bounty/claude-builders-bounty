#!/usr/bin/env bash
# =============================================================================
# changelog.sh — Generate a structured CHANGELOG.md from git history
# -----------------------------------------------------------------------------
# Accepts: no arguments (writes CHANGELOG.md) or a custom output path.
# Behavior:
#   * Finds the last git tag (falls back to the full history if none exists).
#   * Fetches commits since that tag (or all commits if no tags).
#   * Auto-categorizes each commit into: Added / Fixed / Changed / Removed.
#   * Writes a conventional Keep-a-Changelog style CHANGELOG.md.
#
# Categorization (Conventional Commits):
#   Added   -> feat, feature, add, new
#   Fixed   -> fix, bugfix, bug, hotfix
#   Changed -> refactor, perf, chore, docs, style, test, build, ci, dep,
#              update, tweak, improve, migrate
#   Removed -> remove, delete, breaking, drop, deprecate
# =============================================================================
set -euo pipefail

PROJECT_DIR="${1:-.}"
OUTPUT="${2:-CHANGELOG.md}"
cd "$PROJECT_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "ERROR: '$PROJECT_DIR' is not a git repository." >&2
  exit 1
fi

# --- Determine the base ref (last tag, or empty = full history) -------------
BASE_SHA=""
if git tag --sort=-creatordate | head -n 1 >/dev/null 2>&1; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
else
  LAST_TAG=""
fi

if [[ -n "$LAST_TAG" ]]; then
  BASE_SPEC="$LAST_TAG..HEAD"
  RANGE_DESC="since $LAST_TAG"
else
  BASE_SPEC="HEAD"
  RANGE_DESC="full history (no tags found)"
fi

echo "Changelog range: $RANGE_DESC" >&2

# --- Fetch commits with hash + subject --------------------------------------
# Format: <hash>|<subject>
COMMITS=$(git log --pretty=format:'%h|%s' "$BASE_SPEC" 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range." >&2
  echo "# Changelog" > "$OUTPUT"
  echo "" >> "$OUTPUT"
  echo "_(no commits in the selected range)_" >> "$OUTPUT"
  exit 0
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

classify() {
  local subject="$1"
  # Remove conventional commit scope: feat(scope): message
  local body
  body=$(echo "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?: ?//')
  local lower
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^(feat|feature|add|new|introduce)[(:]'; then
    echo "Added:$body"
  elif echo "$lower" | grep -qE '^(fix|bugfix|bug|hotfix|patch)[(:]'; then
    echo "Fixed:$body"
  elif echo "$lower" | grep -qE '^(remove|delete|drop|deprecate|breaking|refactor!)[(:]' \
      || echo "$lower" | grep -qE '(^| )(!):'; then
    echo "Removed:$body"
  else
    echo "Changed:$body"
  fi
}

while IFS='|' read -r hash subject; do
  [[ -z "$hash" ]] && continue
  result=$(classify "$subject")
  category="${result%%:*}"
  clean="${result#*:}"
  case "$category" in
    Added)   ADDED+=("* $clean ([$hash](https://github.com/user/repo/commit/$hash))") ;;
    Fixed)   FIXED+=("* $clean ([$hash](https://github.com/user/repo/commit/$hash))") ;;
    Removed) REMOVED+=("* $clean ([$hash](https://github.com/user/repo/commit/$hash))") ;;
    *)       CHANGED+=("* $clean ([$hash](https://github.com/user/repo/commit/$hash))") ;;
  esac
done <<< "$COMMITS"

# --- Write CHANGELOG.md ------------------------------------------------------
TODAY=$(date +%Y-%m-%d)
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project are documented in this file,"
  echo "generated automatically from git history."
  echo ""
  echo "## [Unreleased] — $TODAY"
  echo ""
  echo "_Range: ${RANGE_DESC}_"
  echo ""
  echo "### Added"
  if [[ ${#ADDED[@]} -eq 0 ]]; then
    echo "- No additions in this range."
  else
    printf '%s\n' "${ADDED[@]}"
  fi
  echo ""
  echo "### Fixed"
  if [[ ${#FIXED[@]} -eq 0 ]]; then
    echo "- No fixes in this range."
  else
    printf '%s\n' "${FIXED[@]}"
  fi
  echo ""
  echo "### Changed"
  if [[ ${#CHANGED[@]} -eq 0 ]]; then
    echo "- No changes in this range."
  else
    printf '%s\n' "${CHANGED[@]}"
  fi
  echo ""
  echo "### Removed"
  if [[ ${#REMOVED[@]} -eq 0 ]]; then
    echo "- Nothing removed in this range."
  else
    printf '%s\n' "${REMOVED[@]}"
  fi
  echo ""
} > "$OUTPUT"

echo "Wrote $OUTPUT (${#ADDED[@]} added, ${#FIXED[@]} fixed, ${#CHANGED[@]} changed, ${#REMOVED[@]} removed)." >&2
exit 0