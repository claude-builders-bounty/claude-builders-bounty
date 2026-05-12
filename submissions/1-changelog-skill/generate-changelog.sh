#!/usr/bin/env bash
# generate-changelog — Generate structured CHANGELOG.md from git history
# Usage: ./generate-changelog.sh [--since <tag>] [--repo <path>]
set -euo pipefail

REPO="${PWD}"
SINCE_TAG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --since) SINCE_TAG="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --help|-h) echo "Usage: generate-changelog.sh [--since <tag>] [--repo <path>]"; exit 0 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

cd "$REPO"

# Find the last tag if not specified
if [ -z "$SINCE_TAG" ]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
fi

echo "Generating changelog since: $SINCE_TAG"
echo ""

# Get commits grouped by type
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS='|' read -r hash subject body; do
  CATEGORY="other"
  CLEAN_SUBJECT=$(echo "$subject" | sed 's/^[a-z]*([^)]*):\s*//' | sed 's/^[a-z]*:\s*//')
  
  case "$subject" in
    feat:*|feature:*|add:*|implement:*|introduce:*|✨|feat\(*)
      CATEGORY="added"
      ;;
    fix:*|bugfix:*|hotfix:*|patch:*|resolve:*|🐛|fix\(*)
      CATEGORY="fixed"
      ;;
    refactor:*|improve:*|update:*|upgrade:*|rework:*|♻️|refactor\(*)
      CATEGORY="changed"
      ;;
    remove:*|delete:*|deprecate:*|drop:*|🔥|remove\(*)
      CATEGORY="removed"
      ;;
    chore:*|docs:*|style:*|test:*|build:*|ci:*|perf:*|📝|docs\(*)
      CATEGORY="other"
      ;;
  esac
  
  SHORT_HASH=$(echo "$hash" | cut -c1-7)
  LINE="- $CLEAN_SUBJECT ($SHORT_HASH)"
  
  case "$CATEGORY" in
    added) ADDED="$ADDED\n$LINE" ;;
    fixed) FIXED="$FIXED\n$LINE" ;;
    changed) CHANGED="$CHANGED\n$LINE" ;;
    removed) REMOVED="$REMOVED\n$LINE" ;;
    *) OTHER="$OTHER\n$LINE" ;;
  esac
done < <(git log "$SINCE_TAG..HEAD" --pretty=format:"%H|%s|%b" --no-merges 2>/dev/null)

# Generate CHANGELOG.md
OUTPUT="# Changelog\n\n"
OUTPUT="$OUTPUT## [Unreleased] - $(date +%Y-%m-%d)\n"

if [ -n "$(echo -e "$ADDED" | tr -d '[:space:]')" ]; then
  OUTPUT="$OUTPUT\n### Added\n$(echo -e "$ADDED" | grep -v '^$')\n"
fi
if [ -n "$(echo -e "$FIXED" | tr -d '[:space:]')" ]; then
  OUTPUT="$OUTPUT\n### Fixed\n$(echo -e "$FIXED" | grep -v '^$')\n"
fi
if [ -n "$(echo -e "$CHANGED" | tr -d '[:space:]')" ]; then
  OUTPUT="$OUTPUT\n### Changed\n$(echo -e "$CHANGED" | grep -v '^$')\n"
fi
if [ -n "$(echo -e "$REMOVED" | tr -d '[:space:]')" ]; then
  OUTPUT="$OUTPUT\n### Removed\n$(echo -e "$REMOVED" | grep -v '^$')\n"
fi
if [ -n "$(echo -e "$OTHER" | tr -d '[:space:]')" ]; then
  OUTPUT="$OUTPUT\n### Other\n$(echo -e "$OTHER" | grep -v '^$')\n"
fi

echo -e "$OUTPUT" > CHANGELOG.md
echo "✅ CHANGELOG.md generated"
echo "   Commit count:" $(git log "$SINCE_TAG..HEAD" --oneline --no-merges 2>/dev/null | wc -l)
