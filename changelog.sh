#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must run inside a git repository" >&2
  exit 1
fi

LAST_TAG=""
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG="$(git describe --tags --abbrev=0)"
  RANGE="$LAST_TAG..HEAD"
else
  RANGE="HEAD"
fi

COMMITS="$(git log --no-merges --date=short --pretty=format:'%H%x09%ad%x09%s' $RANGE)"
NOW="$(date -u +%Y-%m-%d)"

classify() {
  local subject_lc
  subject_lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$subject_lc" in
    feat:*|feature:*|add:*|added:*|implement*|introduce*|*" add "*|*" adds "*|*" implement"*|*" introduce"*) echo "Added" ;;
    fix:*|bug:*|hotfix:*|repair*|correct*|*" fix"*|*" bug"*|*" repair"*|*" correct"*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|drop\ *|*" remove"*|*" delete"*|*" drop "*) echo "Removed" ;;
    refactor:*|chore:*|docs:*|style:*|test:*|ci:*|perf:*|change:*|changed:*|update:*|updated:*|*" update"*|*" refactor"*) echo "Changed" ;;
    *) echo "Changed" ;;
  esac
}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
for section in Added Fixed Changed Removed; do : > "$TMP_DIR/$section"; done

if [ -n "$COMMITS" ]; then
  while IFS=$'\t' read -r sha date subject; do
    [ -n "${sha:-}" ] || continue
    section="$(classify "$subject")"
    short="${sha:0:7}"
    printf -- '- %s (%s, %s)\n' "$subject" "$short" "$date" >> "$TMP_DIR/$section"
  done <<< "$COMMITS"
fi

{
  echo "# Changelog"
  echo
  if [ -n "$LAST_TAG" ]; then
    echo "Generated from commits since tag \`$LAST_TAG\`."
  else
    echo "Generated from repository history; no git tag was found."
  fi
  echo
  echo "## Unreleased - $NOW"
  echo
  for section in Added Fixed Changed Removed; do
    echo "### $section"
    if [ -s "$TMP_DIR/$section" ]; then
      cat "$TMP_DIR/$section"
    else
      echo "- No entries."
    fi
    echo
  done
} > "$OUT_FILE"

echo "Wrote $OUT_FILE"
