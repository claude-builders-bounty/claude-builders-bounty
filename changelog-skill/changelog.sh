#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [output-file]   (default: CHANGELOG.md)
# Lists commits since the last git tag, categorized Added/Fixed/Changed/Removed.
set -euo pipefail

OUT="${1:-CHANGELOG.md}"
REPO_NAME="$(basename "$(git rev-parse --show-toplevel)")"

# Last tag reachable from HEAD; fall back to root commit if no tags exist.
if LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  RANGE_LABEL="all history (no tags found)"
fi

DATE="$(date +%Y-%m-%d)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

categorize() {
  # $1 = commit subject. Prints one of: Added Fixed Changed Removed
  local s
  s="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$s" in
    feat*|add*|*"add "*|*"added"*|*"new "*)          echo "Added" ;;
    fix*|bugfix*|hotfix*|*"fix "*|*"fixed"*|*"bug"*) echo "Fixed" ;;
    revert*|*"remove"*|*"removed"*|*"delete"*)       echo "Removed" ;;
    *)                                               echo "Changed" ;;
  esac
}

{
  echo "# Changelog"
  echo
  echo "## [Unreleased] — ${DATE}"
  echo
  echo "_${REPO_NAME}: commits ${RANGE_LABEL}_"
  echo
} > "$TMP"

for cat in Added Fixed Changed Removed; do
  entries=""
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    hash="${line%% *}"
    subject="${line#* }"
    if [ "$(categorize "$subject")" = "$cat" ]; then
      entries="${entries}- ${subject} (\`${hash}\`)
"
    fi
  done < <(git log "$RANGE" --pretty=format:'%h %s' --no-merges)
  if [ -n "$entries" ]; then
    {
      echo "### ${cat}"
      echo
      printf '%s' "$entries"
      echo
    } >> "$TMP"
  fi
done

# Prepend new section to existing changelog (keep old entries below).
if [ -f "$OUT" ]; then
  { cat "$TMP"; echo; cat "$OUT"; } > "${OUT}.new"
  mv "${OUT}.new" "$OUT"
else
  mv "$TMP" "$OUT"
  trap - EXIT
fi

echo "Wrote $OUT ($(git log "$RANGE" --pretty=oneline --no-merges | wc -l | tr -d ' ') commits ${RANGE_LABEL})"
