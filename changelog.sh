#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from commits since the latest git tag.
# Usage: bash changelog.sh [output-file]

OUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LATEST_TAG" ]; then
  RANGE="$LATEST_TAG..HEAD"
  RANGE_LABEL="since $LATEST_TAG"
else
  RANGE="HEAD"
  RANGE_LABEL="from project history"
fi

COMMITS="$(git log --no-merges --pretty=format:'%s|%h' "$RANGE" 2>/dev/null || true)"
DATE="$(date +%Y-%m-%d)"

category_for() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*) echo "Added" ;;
    fix:*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" bug "*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|deprecated:*|*" remove "*) echo "Removed" ;;
    change:*|changed:*|refactor:*|perf:*|docs:*|test:*|ci:*|chore:*|style:*|build:*) echo "Changed" ;;
    *) echo "Changed" ;;
  esac
}

strip_prefix() {
  printf '%s' "$1" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//'
}

append_section() {
  local section="$1"
  local content="$2"
  printf '### %s\n' "$section"
  if [ -n "$content" ]; then
    printf '%s\n' "$content"
  else
    printf -- '- No changes.\n'
  fi
  printf '\n'
}

added=""
fixed=""
changed=""
removed=""

while IFS='|' read -r subject hash; do
  [ -n "${subject:-}" ] || continue
  clean="$(strip_prefix "$subject")"
  line="- ${clean} (${hash})"
  case "$(category_for "$subject")" in
    Added) added="${added}${line}\n" ;;
    Fixed) fixed="${fixed}${line}\n" ;;
    Removed) removed="${removed}${line}\n" ;;
    *) changed="${changed}${line}\n" ;;
  esac
done <<< "$COMMITS"

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$DATE"
  printf '_Generated from commits %s._\n\n' "$RANGE_LABEL"
  append_section "Added" "$(printf '%b' "$added" | sed '/^$/d')"
  append_section "Fixed" "$(printf '%b' "$fixed" | sed '/^$/d')"
  append_section "Changed" "$(printf '%b' "$changed" | sed '/^$/d')"
  append_section "Removed" "$(printf '%b' "$removed" | sed '/^$/d')"
} > "$OUT_FILE"

echo "Wrote $OUT_FILE"
