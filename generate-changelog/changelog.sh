#!/usr/bin/env bash
set -euo pipefail

# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--tag <tag>] [--repo <path>]

REPO_PATH="${2:-.}"
SINCE_TAG=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag) SINCE_TAG="$2"; shift 2 ;;
    --repo) REPO_PATH="$2"; shift 2 ;;
    *) echo "Usage: $0 [--tag <tag>] [--repo <path>]"; exit 1 ;;
  esac
done

cd "$REPO_PATH"

# Check we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: not a git repository ($REPO_PATH)" >&2
  exit 1
fi

# Determine the tag range
if [ -z "$SINCE_TAG" ]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

RANGE=""
VERSION_HEADER=""
if [ -n "$SINCE_TAG" ]; then
  RANGE="${SINCE_TAG}..HEAD"
  VERSION_HEADER="## [Unreleased] (since ${SINCE_TAG})"
else
  VERSION_HEADER="## [Unreleased]"
fi

# Fetch commits
ALL_COMMITS=$(git log "$RANGE" --pretty=format:"%H||%s||%an||%ad" --date=short 2>/dev/null || true)

if [ -z "$ALL_COMMITS" ]; then
  echo "No commits found${SINCE_TAG:+ since $SINCE_TAG}."
  exit 0
fi

CAT_ADDED=""
CAT_FIXED=""
CAT_CHANGED=""
CAT_REMOVED=""
CAT_OTHER=""

while IFS='||' read -r HASH SUBJECT AUTHOR DATE; do
  [ -z "$HASH" ] && continue
  LINE="- ${SUBJECT} ([${HASH:0:7}](https://github.com/$(git remote get-url origin 2>/dev/null | sed 's/.*:\(.*\)\.git/\1/')/commit/${HASH}))"

  case "$SUBJECT" in
    feat:*|feature:*|add:*|Add*|Added*|implement:*|Implement*)
      CAT_ADDED="${CAT_ADDED}${LINE}
" ;;
    fix:*|bugfix:*|Fix*|Fixed*|patch:*|hotfix:*)
      CAT_FIXED="${CAT_FIXED}${LINE}
" ;;
    refactor:*|Refactor*|chore:*|update:*|Update*|bump:*|Bump*|improve:*)
      CAT_CHANGED="${CAT_CHANGED}${LINE}
" ;;
    remove:*|Remove*|Removed*|deprecate:*|delete:*|Delete*)
      CAT_REMOVED="${CAT_REMOVED}${LINE}
" ;;
    docs:*|test:*|ci:*|style:*|perf:*|build:*)
      # Skip these common prefixes in the "Other" bucket or ignore
      ;;
    *)
      CAT_OTHER="${CAT_OTHER}${LINE}
" ;;
  esac
done <<< "$ALL_COMMITS"

# Build CHANGELOG.md
OUTPUT="# Changelog

${VERSION_HEADER}

"

append_section() {
  local HEADING="$1"
  local CONTENT="$2"
  if [ -n "$CONTENT" ]; then
    OUTPUT="${OUTPUT}### ${HEADING}
${CONTENT}
"
  fi
}

append_section "Added" "$CAT_ADDED"
append_section "Fixed" "$CAT_FIXED"
append_section "Changed" "$CAT_CHANGED"
append_section "Removed" "$CAT_REMOVED"
append_section "Other" "$CAT_OTHER"

echo "$OUTPUT" > CHANGELOG.md
echo "Generated CHANGELOG.md ($(echo "$OUTPUT" | wc -l) lines)"
