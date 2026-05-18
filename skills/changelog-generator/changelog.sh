#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -n "$LAST_TAG" ]; then
  TAG_COMMIT=$(git rev-list -n 1 "$LAST_TAG" 2>/dev/null || true)
  HEAD_COMMIT=$(git rev-parse HEAD)
  if [ "$TAG_COMMIT" = "$HEAD_COMMIT" ]; then
    LAST_TAG=$(git tag --sort=-creatordate | head -2 | tail -1 2>/dev/null || true)
  fi
fi

if [ -z "$LAST_TAG" ]; then
  LAST_TAG=$(git rev-list --max-parents=0 HEAD)
fi

COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%s" 2>/dev/null || true)

{
  echo "# Changelog"
  echo ""

  if [ -z "$COMMITS" ]; then
    echo "No new commits since ${LAST_TAG:0:8}."
    echo ""
  else
    write_section() {
      local label="$1" pattern="$2"
      local matches
      matches=$(echo "$COMMITS" | grep -iE "$pattern" || true)
      if [ -n "$matches" ]; then
        echo ""
        echo "## $label"
        echo "$matches" | sed 's/^/- /'
      fi
    }

    write_section "Added"   "^(add|feature|feat|new)"
    write_section "Fixed"   "^(fix|bugfix|hotfix|patch)"
    write_section "Changed" "^(change|refactor|update|upgrade|bump|migrate|chore)"
    write_section "Removed" "^(remove|delete|deprecate|drop)"

    UNCAT=$(echo "$COMMITS" | grep -viE "^(add|feature|feat|new|fix|bugfix|hotfix|patch|change|refactor|update|upgrade|bump|migrate|chore|remove|delete|deprecate|drop)" || true)
    if [ -n "$UNCAT" ]; then
      echo ""
      echo "## Uncategorized"
      echo "$UNCAT" | sed 's/^/- /'
    fi
  fi
} > "$OUTPUT"

COUNT=$(echo "$COMMITS" | grep -c . || true)
echo "Generated $OUTPUT ($COUNT commits since ${LAST_TAG:0:8})"
