#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: must run inside a git repository" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
TODAY="$(date +%Y-%m-%d)"
VERSION="${LAST_TAG:-Unreleased}"

if [[ -n "$LAST_TAG" ]]; then
  RANGE="$LAST_TAG..HEAD"
else
  RANGE="HEAD"
fi

TMPDIR="$(mktemp -d)"
ADDED="$TMPDIR/added.txt"
FIXED="$TMPDIR/fixed.txt"
CHANGED="$TMPDIR/changed.txt"
REMOVED="$TMPDIR/removed.txt"
: > "$ADDED"
: > "$FIXED"
: > "$CHANGED"
: > "$REMOVED"

categorize_commit() {
  local msg="$1"
  local lower
  lower="$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ ^(feat|add|create|implement)(\(.+\))?:?[[:space:]] ]]; then
    printf '%s\n' "$msg" >> "$ADDED"
  elif [[ "$lower" =~ ^(fix|bug|patch|hotfix)(\(.+\))?:?[[:space:]] ]]; then
    printf '%s\n' "$msg" >> "$FIXED"
  elif [[ "$lower" =~ ^(remove|delete|drop|deprecate)(\(.+\))?:?[[:space:]] ]]; then
    printf '%s\n' "$msg" >> "$REMOVED"
  elif [[ "$lower" =~ ^(refactor|update|change|perf|docs|style|chore)(\(.+\))?:?[[:space:]] ]]; then
    printf '%s\n' "$msg" >> "$CHANGED"
  else
    printf '%s\n' "$msg" >> "$CHANGED"
  fi
}

while IFS= read -r commit; do
  [[ -z "$commit" ]] && continue
  categorize_commit "$commit"
done < <(git log --pretty=format:%s $RANGE)

write_section_from_file() {
  local title="$1"
  local file="$2"
  [[ ! -s "$file" ]] && return 0
  echo "## $title"
  while IFS= read -r entry; do
    echo "- $entry"
  done < "$file"
  echo
}

{
  echo "# CHANGELOG"
  echo
  echo "## [$VERSION] - $TODAY"
  echo
  write_section_from_file "Added" "$ADDED"
  write_section_from_file "Fixed" "$FIXED"
  write_section_from_file "Changed" "$CHANGED"
  write_section_from_file "Removed" "$REMOVED"
} > CHANGELOG.md

rm -rf "$TMPDIR"
echo "Generated CHANGELOG.md from ${LAST_TAG:-full history}."
