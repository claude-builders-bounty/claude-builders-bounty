#!/usr/bin/env bash
set -euo pipefail

# Generate a categorized CHANGELOG.md from git history since the last tag

OUTFILE="${1:-CHANGELOG.md}"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  SINCE="since $LAST_TAG"
else
  RANGE=""
  SINCE="(all commits)"
fi

# Collect commits: hash|subject
COMMITS=$(git log $RANGE --pretty=format:"%h|%s" --no-merges)

if [ -z "$COMMITS" ]; then
  echo "No commits found $SINCE"
  exit 0
fi

ADDED="" FIXED="" CHANGED="" REMOVED=""

while IFS='|' read -r hash subject; do
  entry="- ${subject} (\`${hash}\`)"
  prefix=$(echo "$subject" | grep -oiE '^(feat|fix|chore|refactor|remove|delete)' || echo "")
  case "${prefix,,}" in
    feat)           ADDED+="${entry}"$'\n' ;;
    fix)            FIXED+="${entry}"$'\n' ;;
    remove|delete)  REMOVED+="${entry}"$'\n' ;;
    chore|refactor) CHANGED+="${entry}"$'\n' ;;
    *)              CHANGED+="${entry}"$'\n' ;;
  esac
done <<< "$COMMITS"

DATE=$(date +%Y-%m-%d)

write_section() {
  local title="$1" body="$2"
  if [ -n "$body" ]; then
    echo "### ${title}"
    echo ""
    echo -n "$body"
    echo ""
  fi
}

{
  echo "# Changelog — ${REPO_NAME}"
  echo ""
  echo "## [Unreleased] — ${DATE}"
  echo ""
  write_section "Added" "$ADDED"
  write_section "Fixed" "$FIXED"
  write_section "Changed" "$CHANGED"
  write_section "Removed" "$REMOVED"
  echo "---"
  echo "*Generated $SINCE by [generate-changelog](https://github.com/claude-builders-bounty/claude-builders-bounty)*"
} > "$OUTFILE"

echo "✅ Wrote ${OUTFILE} (${SINCE})"
