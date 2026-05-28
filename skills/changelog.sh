#!/usr/bin/env bash
# generate-changelog — builds CHANGELOG.md entries from git history
# Usage: bash changelog.sh [--since <tag-or-date>] [--until <tag-or-date>] [--output CHANGELOG.md]

set -euo pipefail

SINCE=""
UNTIL="HEAD"
OUTPUT="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --until) UNTIL="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Default: commits since last tag
if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

RANGE="${SINCE:+${SINCE}..}${UNTIL}"
VERSION=$(git describe --tags --abbrev=0 "$UNTIL" 2>/dev/null || echo "Unreleased")
DATE=$(date +%Y-%m-%d)

declare -A SECTIONS
SECTIONS=(
  [Added]=""
  [Fixed]=""
  [Changed]=""
  [Documentation]=""
  [Tests]=""
  [Maintenance]=""
  ["Breaking Changes"]=""
)

classify_commit() {
  local msg="$1"
  case "$msg" in
    feat\(*\)*|feat:*|add:*|Add*) echo "Added" ;;
    fix\(*\)*|fix:*|bug:*|Bug*) echo "Fixed" ;;
    refactor\(*\)*|refactor:*|perf\(*\)*|perf:*|style:*) echo "Changed" ;;
    docs\(*\)*|docs:*|doc:*) echo "Documentation" ;;
    test\(*\)*|test:*|tests:*) echo "Tests" ;;
    chore\(*\)*|chore:*|build:*|ci:*|deps:*) echo "Maintenance" ;;
    BREAKING*|breaking:*) echo "Breaking Changes" ;;
    *) echo "Changed" ;;
  esac
}

while IFS='|' read -r hash msg; do
  [[ -z "$hash" ]] && continue
  section=$(classify_commit "$msg")
  short_msg="${msg#*: }"
  short_msg="${short_msg#*\) }"
  SECTIONS[$section]+="- ${short_msg} (${hash})"$'\n'
done < <(git log --pretty=format:"%h|%s" ${RANGE} 2>/dev/null)

{
  echo "## [${VERSION}] — ${DATE}"
  echo ""
  for section in "Breaking Changes" Added Fixed Changed Documentation Tests Maintenance; do
    if [[ -n "${SECTIONS[$section]}" ]]; then
      echo "### ${section}"
      echo ""
      echo "${SECTIONS[$section]}"
    fi
  done
} > /tmp/_changelog_new.md

if [[ -f "$OUTPUT" ]]; then
  # Prepend new section above existing content
  cat /tmp/_changelog_new.md "$OUTPUT" > /tmp/_changelog_merged.md
  mv /tmp/_changelog_merged.md "$OUTPUT"
else
  echo "# Changelog" > "$OUTPUT"
  echo "" >> "$OUTPUT"
  cat /tmp/_changelog_new.md >> "$OUTPUT"
fi

echo "✅ Changelog written to $OUTPUT"
