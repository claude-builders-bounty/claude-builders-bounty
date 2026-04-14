#!/usr/bin/env bash
set -euo pipefail

SINCE_TAG="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "")}"
OUTPUT="${2:-CHANGELOG.md}"

# Detect repo name from remote
REPO_URL=$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' | sed 's|.*/||') || REPO_URL=""

# Get commits
if [[ -n "$SINCE_TAG" ]]; then
  TAG_DATE=$(git log -1 --format=%ci "$SINCE_TAG" 2>/dev/null | cut -d' ' -f1)
  COMMITS=$(git log --since="$TAG_DATE" --pretty=format:"%s||%h||%an||%ae" HEAD 2>/dev/null | head -100)
  HEADER_LINE="## [$SINCE_TAG]"
else
  COMMITS=$(git log --pretty=format:"%s||%h||%an||%ae" -100 HEAD 2>/dev/null)
  HEADER_LINE="## [Unreleased]"
fi

# Init sections
ADDED="" FIXED="" CHANGED="" REMOVED=""

# Parse
while IFS='||' read -r subject hash author email; do
  [[ -z "$subject" ]] && continue
  ref_link=""
  if [[ -n "$REPO_URL" && -n "$hash" ]]; then
    ref_link="([\`$hash\`](https://github.com/$REPO_URL/commit/$hash))"
  fi
  line="- $subject $ref_link"

  case "$subject" in
    feat!*|*feat:*|*feat\(*)      ) ADDED="${ADDED}"$'\n'"  $line" ;;
    fix!*|*fix:*|*fix\(*)          ) FIXED="${FIXED}"$'\n'"  $line" ;;
    refactor!*|*refactor:*|perf!*|*perf:*|test!*|*test:*|style!*|*style:*|ci!*|*ci:*|docs!*) 
                                    CHANGED="${CHANGED}"$'\n'"  $line" ;;
    *BREAKING*|*deprecated*|remove!*|*remove:*|*chore\(removed\):*) 
                                    REMOVED="${REMOVED}"$'\n'"  $line" ;;
    *)                              CHANGED="${CHANGED}"$'\n'"  $line" ;;
  esac
done <<< "$COMMITS"

# Write output
{
  echo "# Changelog"
  echo
  echo "$HEADER_LINE"
  echo
  [[ -n "$ADDED" ]]   && echo "### Added"   && echo -e "$ADDED"   && echo
  [[ -n "$FIXED" ]]   && echo "### Fixed"   && echo -e "$FIXED"   && echo
  [[ -n "$CHANGED" ]] && echo "### Changed" && echo -e "$CHANGED" && echo
  [[ -n "$REMOVED" ]] && echo "### Removed" && echo -e "$REMOVED" && echo
  echo "_Generated $(date '+%Y-%m-%d') by changelog-generator skill_"
} > "$OUTPUT"

echo "CHANGELOG written to $OUTPUT"
