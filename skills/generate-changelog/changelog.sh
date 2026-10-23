#!/usr/bin/env bash
# Auto-generates a structured CHANGELOG.md from git commits since the last tag
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  HEADER_RANGE="Since ${LAST_TAG}"
else
  RANGE="HEAD"
  HEADER_RANGE="Initial Release"
fi

DATE_STR=$(date +%Y-%m-%d)
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  [ -z "$line" ] && continue
  HASH=$(echo "$line" | awk '{print $1}')
  MSG=$(echo "$line" | cut -d' ' -f2-)
  LOWER=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')

  if [[ "$LOWER" =~ ^(feat|add|new|create|implement) ]] || [[ "$LOWER" == *"add "* ]]; then
    ADDED+="- ${MSG} (\${HASH})\n"
  elif [[ "$LOWER" =~ ^(fix|bug|hotfix|patch|resolve) ]] || [[ "$LOWER" == *"fix "* ]]; then
    FIXED+="- ${MSG} (\${HASH})\n"
  elif [[ "$LOWER" =~ ^(remove|delete|drop|deprecate|clean) ]] || [[ "$LOWER" == *"remove "* ]]; then
    REMOVED+="- ${MSG} (\${HASH})\n"
  else
    CHANGED+="- ${MSG} (\${HASH})\n"
  fi
done < <(git log "$RANGE" --oneline --no-merges)

{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased] - ${DATE_STR} (${HEADER_RANGE})"
  echo ""
  echo "### Added"
  if [ -n "$ADDED" ]; then echo -e "$ADDED"; else echo "- None"; echo ""; fi
  echo "### Fixed"
  if [ -n "$FIXED" ]; then echo -e "$FIXED"; else echo "- None"; echo ""; fi
  echo "### Changed"
  if [ -n "$CHANGED" ]; then echo -e "$CHANGED"; else echo "- None"; echo ""; fi
  echo "### Removed"
  if [ -n "$REMOVED" ]; then echo -e "$REMOVED"; else echo "- None"; echo ""; fi
} > "$OUTPUT_FILE"

echo "Generated structured changelog at $OUTPUT_FILE"
