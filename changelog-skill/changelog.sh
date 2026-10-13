#!/usr/bin/env bash
set -euo pipefail

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  HEADER="## [Unreleased] (since ${LAST_TAG}) - $(date +%Y-%m-%d)"
else
  RANGE="HEAD"
  HEADER="## [Unreleased] - $(date +%Y-%m-%d)"
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  [ -z "$line" ] && continue
  if echo "$line" | grep -qiE "^[a-f0-9]+ (feat|add|new)"; then
    ADDED="${ADDED}- ${line}
"
  elif echo "$line" | grep -qiE "^[a-f0-9]+ (fix|bug|hotfix|patch)"; then
    FIXED="${FIXED}- ${line}
"
  elif echo "$line" | grep -qiE "^[a-f0-9]+ (remove|delete|drop|deprecate)"; then
    REMOVED="${REMOVED}- ${line}
"
  else
    CHANGED="${CHANGED}- ${line}
"
  fi
done < <(git log $RANGE --oneline --no-merges -n 50)

{
  echo "# Changelog"
  echo ""
  echo "$HEADER"
  echo ""
  echo "### Added"
  printf "%b" "${ADDED:-- None
}"
  echo ""
  echo "### Fixed"
  printf "%b" "${FIXED:-- None
}"
  echo ""
  echo "### Changed"
  printf "%b" "${CHANGED:-- None
}"
  echo ""
  echo "### Removed"
  printf "%b" "${REMOVED:-- None
}"
} > CHANGELOG.md

echo "✅ Generated CHANGELOG.md successfully."
