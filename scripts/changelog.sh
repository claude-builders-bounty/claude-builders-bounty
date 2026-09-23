#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh [output-file]     # defaults to ./CHANGELOG.md
#
# Collects commits since the most recent git tag (or the full history when
# the repo has no tags), auto-categorizes them into Added / Fixed / Changed
# / Removed, and writes a Keep-a-Changelog style markdown file.

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "error: not inside a git repository" >&2
  exit 1
fi

REPO="$(basename "$(git rev-parse --show-toplevel)")"
TODAY="$(date +%Y-%m-%d)"

if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG="$(git describe --tags --abbrev=0)"
  RANGE="${LAST_TAG}..HEAD"
  RANGE_LABEL="since tag \`${LAST_TAG}\`"
else
  RANGE="HEAD"
  RANGE_LABEL="full history (no tags found)"
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

categorize() {
  local subject="$1" hash="$2"
  local bullet="- \`$hash\` $subject"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  # Conventional-commit prefixes win first (matched on the raw subject).
  case "$lower" in
    feat:*|feat\(*)
      ADDED+=("$bullet"); return ;;
    fix:*|fix\(*)
      FIXED+=("$bullet"); return ;;
    docs:*|docs\(*|chore:*|chore\(*|test:*|test\(*|ci:*|ci\(*|build:*|style:*|refactor:*|perf:*)
      CHANGED+=("$bullet"); return ;;
  esac
  # Keyword heuristics.
  case "$lower" in
    *remov*|*delet*|*deprecat*)
      REMOVED+=("$bullet") ;;
    *fix*|*bug*|*patch*|*hotfix*|*resolv*|*correct*)
      FIXED+=("$bullet") ;;
    *add*|*new\ *|*featur*|*introduc*|*implement*|*support*|*creat*)
      ADDED+=("$bullet") ;;
    *)
      CHANGED+=("$bullet") ;;
  esac
}

COUNT=0
while IFS='|' read -r hash subject; do
  [ -z "${hash:-}" ] && continue
  COUNT=$((COUNT + 1))
  categorize "$subject" "$hash"
done < <(git log "$RANGE" --no-merges --pretty=tformat:'%h|%s')

print_section() {
  local title="$1"; shift
  [ "$#" -eq 0 ] && return 0
  printf '### %s\n\n' "$title"
  printf '%s\n' "$@"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes to `%s` will be documented in this file.\n\n' "$REPO"
  printf '## [Unreleased] - %s\n\n' "$TODAY"
  if [ "$COUNT" -eq 0 ]; then
    printf '_No new commits %s._\n' "$RANGE_LABEL"
  else
    printf '_%d commit(s) %s._\n\n' "$COUNT" "$RANGE_LABEL"
    if [ "${#ADDED[@]}" -gt 0 ]; then print_section "Added" "${ADDED[@]}"; fi
    if [ "${#FIXED[@]}" -gt 0 ]; then print_section "Fixed" "${FIXED[@]}"; fi
    if [ "${#CHANGED[@]}" -gt 0 ]; then print_section "Changed" "${CHANGED[@]}"; fi
    if [ "${#REMOVED[@]}" -gt 0 ]; then print_section "Removed" "${REMOVED[@]}"; fi
  fi
} > "$OUTPUT"

echo "Wrote $COUNT categorized commit(s) to $OUTPUT"
