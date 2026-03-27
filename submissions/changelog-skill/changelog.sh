#!/bin/bash
set -e

LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
VERSION=${LATEST_TAG:-"Unreleased"}
DATE=$(date +%Y-%m-%d)

if [ -n "$LATEST_TAG" ]; then
  COMMITS=$(git log --oneline --pretty=format:"%s" "$LATEST_TAG"..HEAD 2>/dev/null)
else
  COMMITS=$(git log --oneline --pretty=format:"%s" 2>/dev/null)
fi

if [ -z "$COMMITS" ]; then
  echo "No commits found since $VERSION"
  exit 0
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
  case "$line" in
    feat:*|feat\(*|add*|Add*|new*|New*|create*|Create*|implement*|Implement*)
      ADDED="$ADDED\n- $line" ;;
    fix:*|fix\(*|bug*|Bug*|patch*|Patch*|resolve*|Resolve*)
      FIXED="$FIXED\n- $line" ;;
    refactor:*|refactor\(*|update*|Update*|improve*|Improve*|change*|Change*|enhance*|Enhance*|chore:*|chore\(*)
      CHANGED="$CHANGED\n- $line" ;;
    remove*|Remove*|delete*|Delete*|drop*|Drop*|deprecate*|Deprecate*)
      REMOVED="$REMOVED\n- $line" ;;
    *)
      OTHER="$OTHER\n- $line" ;;
  esac
done <<< "$COMMITS"

{
  echo "# Changelog"
  echo ""
  echo "## [$VERSION] - $DATE"
  [ -n "$ADDED" ] && echo -e "\n### Added$ADDED"
  [ -n "$FIXED" ] && echo -e "\n### Fixed$FIXED"
  [ -n "$CHANGED" ] && echo -e "\n### Changed$CHANGED"
  [ -n "$REMOVED" ] && echo -e "\n### Removed$REMOVED"
  [ -n "$OTHER" ] && echo -e "\n### Other$OTHER"
} > CHANGELOG.md

TOTAL=$(echo "$COMMITS" | wc -l | tr -d ' ')
echo "Generated CHANGELOG.md with $TOTAL commits categorized into sections."
echo "Version: $VERSION | Date: $DATE"
