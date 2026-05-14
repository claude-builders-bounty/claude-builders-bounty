#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
}
cd "$REPO_ROOT"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
  SINCE_LABEL="since $LAST_TAG"
else
  RANGE="HEAD"
  SINCE_LABEL="from repository start"
fi

if [ -z "$(git log --format=%H $RANGE 2>/dev/null | head -1)" ]; then
  {
    echo "# Changelog"
    echo
    echo "No commits found $SINCE_LABEL."
  } > "$OUT_FILE"
  echo "Wrote $OUT_FILE"
  exit 0
fi

VERSION="${CHANGELOG_VERSION:-Unreleased}"
DATE="$(date +%Y-%m-%d)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

git log --reverse --no-merges --format='%s%n%b%x1e' $RANGE > "$TMP"

category_for() {
  local msg="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$msg" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" added "*|*" implement "*|*" introduce "*) echo "Added" ;;
    fix:*|bugfix:*|hotfix:*|*" fix "*|*" fixed "*|*" repair "*|*" resolve "*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|*" remove "*|*" removed "*|*" delete "*) echo "Removed" ;;
    change:*|changed:*|update:*|updated:*|refactor:*|perf:*|docs:*|test:*|chore:*|ci:*|style:*|build:*|*" update "*|*" refactor "*) echo "Changed" ;;
    *) echo "Changed" ;;
  esac
}

clean_subject() {
  printf '%s' "$1" \
    | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//' \
    | sed -E 's/^[[:space:]]+|[[:space:]]+$//g'
}

declare -a ADDED FIXED CHANGED REMOVED
while IFS= read -r subject; do
  [ -z "$subject" ] && continue
  item="$(clean_subject "$subject")"
  [ -z "$item" ] && item="$subject"
  case "$(category_for "$subject")" in
    Added) ADDED+=("$item") ;;
    Fixed) FIXED+=("$item") ;;
    Removed) REMOVED+=("$item") ;;
    *) CHANGED+=("$item") ;;
  esac
done < <(git log --reverse --no-merges --format='%s' $RANGE)

write_section() {
  local title="$1"; shift
  local items=("$@")
  echo "### $title"
  echo
  if [ "${#items[@]}" -eq 0 ]; then
    echo "- None"
  else
    local item
    for item in "${items[@]}"; do
      echo "- $item"
    done
  fi
  echo
}

{
  echo "# Changelog"
  echo
  echo "## [$VERSION] - $DATE"
  echo
  echo "Generated from git history $SINCE_LABEL."
  echo
  write_section "Added" "${ADDED[@]}"
  write_section "Fixed" "${FIXED[@]}"
  write_section "Changed" "${CHANGED[@]}"
  write_section "Removed" "${REMOVED[@]}"
} > "$OUT_FILE"

echo "Wrote $OUT_FILE"
