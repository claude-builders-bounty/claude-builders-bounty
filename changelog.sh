#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [output-file]

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

LATEST_TAG=""
if LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LATEST_TAG}..HEAD"
  RANGE_LABEL="since ${LATEST_TAG}"
else
  RANGE="HEAD"
  RANGE_LABEL="from the beginning of this repository"
fi

COMMITS=$(git log --no-merges --pretty=format:'%s|%h' ${RANGE})
DATE=$(date +%Y-%m-%d)

# Temporary category files keep the script POSIX-tool friendly and dependency-free.
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT
: > "$TMP_DIR/added"
: > "$TMP_DIR/fixed"
: > "$TMP_DIR/changed"
: > "$TMP_DIR/removed"

categorize_commit() {
  local subject="$1"
  local lower
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')

  case "$lower" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*|*" added "*)
      printf 'added'
      ;;
    fix:*|bugfix:*|bug:*|*" fix "*|*" fixes "*|*" fixed "*|*" bug "*)
      printf 'fixed'
      ;;
    remove:*|remove\ *|removed:*|removed\ *|delete:*|delete\ *|deleted:*|deleted\ *|deprecate:*|deprecate\ *|deprecated:*|deprecated\ *|*" remove "*|*" removed "*|*" delete "*|*" deleted "*)
      printf 'removed'
      ;;
    change:*|changed:*|refactor:*|perf:*|docs:*|style:*|test:*|chore:*|ci:*|build:*|*)
      printf 'changed'
      ;;
  esac
}

if [ -n "$COMMITS" ]; then
  while IFS='|' read -r subject hash; do
    [ -n "$subject" ] || continue
    category=$(categorize_commit "$subject")
    printf -- '- %s (%s)\n' "$subject" "$hash" >> "$TMP_DIR/$category"
  done <<EOF_COMMITS
$COMMITS
EOF_COMMITS
fi

write_section() {
  local title="$1"
  local file="$2"
  printf '\n### %s\n\n' "$title"
  if [ -s "$file" ]; then
    cat "$file"
  else
    printf -- '- No changes.\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes generated from git history.\n\n'
  printf '## Unreleased - %s\n\n' "$DATE"
  printf '_Changes %s._\n' "$RANGE_LABEL"
  write_section 'Added' "$TMP_DIR/added"
  write_section 'Fixed' "$TMP_DIR/fixed"
  write_section 'Changed' "$TMP_DIR/changed"
  write_section 'Removed' "$TMP_DIR/removed"
} > "$OUTPUT_FILE"

printf 'Generated %s using commits %s.\n' "$OUTPUT_FILE" "$RANGE_LABEL"
