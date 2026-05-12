#!/usr/bin/env bash

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_LABEL="since ${LAST_TAG}"
else
  RANGE=""
  RANGE_LABEL="from repository history"
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "error: repository has no commits" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

ADDED="$TMP_DIR/added.md"
FIXED="$TMP_DIR/fixed.md"
CHANGED="$TMP_DIR/changed.md"
REMOVED="$TMP_DIR/removed.md"
touch "$ADDED" "$FIXED" "$CHANGED" "$REMOVED"

normalize_subject() {
  printf '%s' "$1" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//'
}

category_for_subject() {
  subject_lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject_lc" in
    feat:*|feat\(*|add:*|add\(*|added:*|implement:*|implement\(*)
      printf 'added'
      ;;
    fix:*|fix\(*|fixed:*|bug:*|bugfix:*|patch:*)
      printf 'fixed'
      ;;
    remove:*|remove\(*|removed:*|delete:*|delete\(*|deleted:*|drop:*|drop\(*|deprecate:*)
      printf 'removed'
      ;;
    *)
      printf 'changed'
      ;;
  esac
}

if [ -n "$RANGE" ]; then
  LOG_COMMAND=(git log "$RANGE" --no-merges --reverse --pretty=format:'%h%x09%s')
else
  LOG_COMMAND=(git log --no-merges --reverse --pretty=format:'%h%x09%s')
fi

while IFS=$'\t' read -r hash subject || [ -n "${hash:-}" ]; do
  [ -n "$hash" ] || continue

  category="$(category_for_subject "$subject")"
  clean_subject="$(normalize_subject "$subject")"
  line="- ${clean_subject} (${hash})"

  case "$category" in
    added) printf '%s\n' "$line" >> "$ADDED" ;;
    fixed) printf '%s\n' "$line" >> "$FIXED" ;;
    removed) printf '%s\n' "$line" >> "$REMOVED" ;;
    *) printf '%s\n' "$line" >> "$CHANGED" ;;
  esac
done < <("${LOG_COMMAND[@]}")

write_section() {
  title="$1"
  file="$2"

  printf '## %s\n\n' "$title"
  if [ -s "$file" ]; then
    cat "$file"
  else
    printf -- '- No changes.\n'
  fi
  printf '\n\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated on %s for commits %s.\n\n' "$(date +%Y-%m-%d)" "$RANGE_LABEL"
  write_section "Added" "$ADDED"
  write_section "Fixed" "$FIXED"
  write_section "Changed" "$CHANGED"
  write_section "Removed" "$REMOVED"
} > "$OUTPUT_FILE"

echo "Wrote ${OUTPUT_FILE}"
