#!/usr/bin/env bash
# generate-changelog.sh — Produce a structured CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [REPO_PATH] [FROM_TAG]
#   REPO_PATH: Path to git repo (default: current directory)
#   FROM_TAG:  Starting tag/ref (default: last tag, or first commit if none)
set -euo pipefail

REPO="${1:-.}"
FROM_TAG="${2:-}"
cd "$REPO"

# Ensure we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not a git repository" >&2
  exit 1
fi

# Determine the log range
if [ -n "$FROM_TAG" ]; then
  LAST_TAG="$FROM_TAG"
  LOG_RANGE="$FROM_TAG..HEAD"
else
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [ -z "$LAST_TAG" ]; then
    # No tags: include all commits on current branch from the beginning
    LOG_RANGE="HEAD"
  else
    LOG_RANGE="$LAST_TAG..HEAD"
  fi
fi

# Collect commits: hash|subject|author
COMMITS=$(git log "$LOG_RANGE" --pretty=format:"%H|%s|%an" --no-merges 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
  echo "No new commits found since ${LAST_TAG:-beginning}"
  exit 0
fi

# Temporary files for each category
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
touch "$TMPDIR/added" "$TMPDIR/fixed" "$TMPDIR/changed" "$TMPDIR/deprecated" "$TMPDIR/removed" "$TMPDIR/security"

while IFS='|' read -r hash subject author; do
  # Only append PR number if not already in the subject line
  entry="- ${subject} by ${author}"

  # Categorize by conventional-commit prefix (case-insensitive)
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
  sep='[:(. ]'
  if echo "$lower" | grep -qE '^(feat|feature|add)'"$sep" || echo "$lower" | grep -qE '^added'"$sep"; then
    echo "$entry" >> "$TMPDIR/added"
  elif echo "$lower" | grep -qE '^(fix|bugfix|patch)'"$sep" || echo "$lower" | grep -qE '^fixed'"$sep"; then
    echo "$entry" >> "$TMPDIR/fixed"
  elif echo "$lower" | grep -qE '^(refactor|change|update|chore|docs|test|ci|build|perf)'"$sep"; then
    echo "$entry" >> "$TMPDIR/changed"
  elif echo "$lower" | grep -qE '^(remove|delete)'"$sep" || echo "$lower" | grep -qE '^removed'"$sep"; then
    echo "$entry" >> "$TMPDIR/removed"
  elif echo "$lower" | grep -qE '^deprecate'"$sep" || echo "$lower" | grep -qE '^deprecated'"$sep"; then
    echo "$entry" >> "$TMPDIR/deprecated"
  elif echo "$lower" | grep -qE '^security'"$sep"; then
    echo "$entry" >> "$TMPDIR/security"
  # Fallback: check for non-prefixed conventional verbs
  elif echo "$lower" | grep -qE '^(add|added|new)[ (]'; then
    echo "$entry" >> "$TMPDIR/added"
  elif echo "$lower" | grep -qE '^(fix|fixed|resolve|resolved)[ (]'; then
    echo "$entry" >> "$TMPDIR/fixed"
  elif echo "$lower" | grep -qE '^(remove|removed|delete|deleted)[ (]'; then
    echo "$entry" >> "$TMPDIR/removed"
  else
    echo "$entry" >> "$TMPDIR/changed"
  fi
done <<< "$COMMITS"

# Build the changelog section
{
  echo "## [Unreleased]"
  echo ""

  for cat in added fixed changed deprecated removed security; do
    if [ -s "$TMPDIR/$cat" ]; then
      # Capitalize category name
      cat_name=$(echo "$cat" | sed 's/.*/\u&/')
      echo "### $cat_name"
      # Reverse so newest first
      tac "$TMPDIR/$cat"
      echo ""
    fi
  done
} > "$TMPDIR/new_section"

# Merge with existing CHANGELOG.md or create new one
CHANGELOG="CHANGELOG.md"
if [ -f "$CHANGELOG" ]; then
  # Prepend new section after the header
  {
    head -1 "$CHANGELOG"  # # Changelog
    echo ""
    cat "$TMPDIR/new_section"
    tail -n +2 "$CHANGELOG"  # rest of file (skip header)
  } > "$CHANGELOG.tmp" && mv "$CHANGELOG.tmp" "$CHANGELOG"
else
  {
    echo "# Changelog"
    echo ""
    cat "$TMPDIR/new_section"
  } > "$CHANGELOG"
fi

echo "CHANGELOG.md updated with $(echo "$COMMITS" | wc -l) commits since ${LAST_TAG:-beginning}"
