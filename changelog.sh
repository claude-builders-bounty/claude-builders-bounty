#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from commits since the last git tag.
# Usage: ./changelog.sh [output-file]

OUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

LAST_TAG=""
if LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  RANGE="${LAST_TAG}..HEAD"
  SINCE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  SINCE_LABEL="from repository history"
fi

COMMITS="$(git log --reverse --pretty=format:'%s%x09%h' "$RANGE")"
DATE="$(date +%Y-%m-%d)"

categorize() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    revert*|remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|*" remove "*|*" deleted "*)
      printf 'Removed'
      ;;
    fix:*|fixed:*|bugfix:*|hotfix:*|*" fix "*|*" bug "*)
      printf 'Fixed'
      ;;
    change:*|changed:*|update:*|updated:*|refactor:*|chore:*|docs:*|doc:*|style:*|test:*|ci:*|build:*|perf:*)
      printf 'Changed'
      ;;
    feat:*|feature:*|add:*|added:*|new:*|*" add "*)
      printf 'Added'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

format_subject() {
  local subject="$1"
  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')"
  printf '%s' "$subject" | sed -E 's/^./\U&/'
}

{
  printf '# Changelog\n\n'
  printf '## [%s] - %s\n\n' "Unreleased" "$DATE"
  printf '_Generated from git commits %s._\n\n' "$SINCE_LABEL"

  for category in Added Fixed Changed Removed; do
    printf '### %s\n\n' "$category"
    found=0
    while IFS=$'\t' read -r subject hash; do
      [ -n "${subject:-}" ] || continue
      if [ "$(categorize "$subject")" = "$category" ]; then
        printf -- '- %s (%s)\n' "$(format_subject "$subject")" "$hash"
        found=1
      fi
    done <<< "$COMMITS"
    if [ "$found" -eq 0 ]; then
      printf -- '- No changes.\n'
    fi
    printf '\n'
  done
} > "$OUT_FILE"

echo "Wrote ${OUT_FILE} (${SINCE_LABEL})"
