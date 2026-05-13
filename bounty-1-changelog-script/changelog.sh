#!/bin/bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
set -e

PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
  COMMITS=$(git log --oneline 2>/dev/null || echo "")
  if [ -z "$COMMITS" ]; then
    echo "Error: No commits found and no git tags exist."
    exit 1
  fi
  echo "No tags found — using all commits."
  RANGE="HEAD"
  TAG_LINE="(initial release — no prior tag)"
else
  echo "Using commits since tag: $LAST_TAG"
  RANGE="$LAST_TAG..HEAD"
  TAG_LINE="Changes since $LAST_TAG"
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  COMMIT_HASH=$(echo "$line" | awk '{print $1}')
  COMMIT_MSG=$(echo "$line" | cut -d' ' -f2-)

  FIRST_WORD=$(echo "$COMMIT_MSG" | awk '{print $1}' | tr '[:upper:]' '[:lower:]' | sed 's/://g')

  BODY="${COMMIT_MSG#* }"
  [ -z "$BODY" ] && BODY="$COMMIT_MSG"

  ENTRY="- $BODY ($COMMIT_HASH)"

  case "$FIRST_WORD" in
    add|added|feature|feat)
      ADDED="$ADDED\n$ENTRY"
      ;;
    fix|fixed|bugfix|bug|hotfix|patch)
      FIXED="$FIXED\n$ENTRY"
      ;;
    change|changed|update|updated|refactor|improve|improved)
      CHANGED="$CHANGED\n$ENTRY"
      ;;
    remove|removed|delete|deleted|deprecate|deprecated|drop)
      REMOVED="$REMOVED\n$ENTRY"
      ;;
    *)
      CHANGED="$CHANGED\n$ENTRY"
      ;;
  esac
done < <(git log "$RANGE" --oneline --no-merges 2>/dev/null || echo "")

OUTPUT="# Changelog\n\n## $TAG_LINE\n"

[ -n "$ADDED" ] && OUTPUT="$OUTPUT\n### Added\n$ADDED\n"
[ -n "$FIXED" ] && OUTPUT="$OUTPUT\n### Fixed\n$FIXED\n"
[ -n "$CHANGED" ] && OUTPUT="$OUTPUT\n### Changed\n$CHANGED\n"
[ -n "$REMOVED" ] && OUTPUT="$OUTPUT\n### Removed\n$REMOVED\n"

echo -e "$OUTPUT" > CHANGELOG.md
echo "Generated CHANGELOG.md"
