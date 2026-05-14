#!/usr/bin/env bash
set -euo pipefail

# CHANGELOG Generator
# Usage: bash changelog.sh [path-to-repo]
# Generates a structured CHANGELOG.md for the repository.

REPO_DIR="${1:-.}"
cd "$REPO_DIR"

# Ensure it's a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository: $REPO_DIR"
  exit 1
fi

# Get the repo name
REPO_SLUG=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:\/]//' | sed 's/\.git$//' | sed 's/.*@//' | sed 's/\/\/.*@/\//')
[ -z "$REPO_SLUG" ] && REPO_SLUG=$(basename "$(git rev-parse --show-toplevel)")

# Get the last tag (fallback to first commit if no tags)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

echo "   Generating for $REPO_SLUG"
echo "   Base: $LAST_TAG → HEAD"
echo ""

# Get commits since last tag
COMMITS=$(git log "$LAST_TAG..HEAD" --pretty=format:"%H@@%s@@%aI" --no-merges 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
  echo "No new commits since $LAST_TAG."
  exit 0
fi

# Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  [ -z "$line" ] && continue
  
  HASH=$(echo "$line" | awk -F'@@' '{print $1}')
  MSG=$(echo "$line" | awk -F'@@' '{print $2}')
  DATE=$(echo "$line" | awk -F'@@' '{print $3}' | cut -d'T' -f1)

  SHORT_HASH=$(echo "$HASH" | head -c 7)

  # Categorize by conventional commit prefix
  CATEGORY="Changed"  # default
  BODY=""
  
  case "$MSG" in
    feat!*|feat:*)
      CATEGORY="Added"
      BODY=$(echo "$MSG" | sed -E 's/^feat(!?)(\([^)]*\))?:\s*//')
      ;;
    fix!*|fix:*)
      CATEGORY="Fixed"
      BODY=$(echo "$MSG" | sed -E 's/^fix(!?)(\([^)]*\))?:\s*//')
      ;;
    remove!*|remove:*|deprecate!*|deprecate:*)
      CATEGORY="Removed"
      BODY=$(echo "$MSG" | sed -E 's/^(remove|deprecate)(!?)(\([^)]*\))?:\s*//')
      ;;
    *!*)
      # Breaking change (any type with !)
      CATEGORY="Changed"
      BODY=$(echo "$MSG" | sed -E 's/^[a-z]+(!?)(\([^)]*\))?:\s*//')
      [ -z "$BODY" ] && BODY="$MSG"
      ;;
    refactor*|perf*|style*|chore*|docs*|test*|build*|ci*|revert*)
      CATEGORY="Changed"
      BODY=$(echo "$MSG" | sed -E 's/^[a-z]+(!?)(\([^)]*\))?:\s*//')
      ;;
    add*|create*|implement*|support*)
      CATEGORY="Added"
      BODY="$MSG"
      ;;
    fix*|correct*|patch*)
      CATEGORY="Fixed"
      BODY="$MSG"
      ;;
    *)
      CATEGORY="Changed"
      BODY="$MSG"
      ;;
  esac

  ENTRY="  - $BODY ([$SHORT_HASH](https://github.com/$REPO_SLUG/commit/$HASH))"

  case "$CATEGORY" in
    Added)   ADDED="$ADDED\n$ENTRY" ;;
    Fixed)   FIXED="$FIXED\n$ENTRY" ;;
    Removed) REMOVED="$REMOVED\n$ENTRY" ;;
    *)       CHANGED="$CHANGED\n$ENTRY" ;;
  esac
done <<< "$COMMITS"

# Get version from latest tag or date
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")
DATE_NOW=$(date +%Y-%m-%d)

# Generate CHANGELOG.md
OUTPUT="# Changelog\n\n## [$VERSION] - $DATE_NOW\n"

[ -n "$(echo -e "$ADDED" | tr -d ' \n')" ] && OUTPUT="$OUTPUT\n### Added\n$ADDED\n"
[ -n "$(echo -e "$FIXED" | tr -d ' \n')" ] && OUTPUT="$OUTPUT\n### Fixed\n$FIXED\n"
[ -n "$(echo -e "$CHANGED" | tr -d ' \n')" ] && OUTPUT="$OUTPUT\n### Changed\n$CHANGED\n"
[ -n "$(echo -e "$REMOVED" | tr -d ' \n')" ] && OUTPUT="$OUTPUT\n### Removed\n$REMOVED\n"

# Write file
echo -e "$OUTPUT" > CHANGELOG.md

echo "✅ CHANGELOG.md generated successfully!"
echo ""
head -30 CHANGELOG.md
