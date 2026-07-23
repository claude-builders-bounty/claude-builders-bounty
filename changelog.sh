#!/usr/bin/env bash
set -euo pipefail

CHANGELOG_FILE="${1:-CHANGELOG.md}"
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)"

echo "# Changelog" > "$CHANGELOG_FILE"
echo "" >> "$CHANGELOG_FILE"

TAG_DATE=$(git log -1 --format=%ai "$LAST_TAG" 2>/dev/null || date)
echo "## [$LAST_TAG] - $TAG_DATE" >> "$CHANGELOG_FILE"
echo "" >> "$CHANGELOG_FILE"

declare -A SECTIONS
SECTIONS[Added]=""
SECTIONS[Fixed]=""
SECTIONS[Changed]=""
SECTIONS[Removed]=""

while IFS= read -r line; do
  msg="${line#* }"
  msg_lower="$(echo "$msg" | tr '[:upper:]' '[:lower:]')"
  category="Changed"
  if echo "$msg_lower" | grep -qE '^add|^feat|^new|^create|^implement'; then
    category="Added"
  elif echo "$msg_lower" | grep -qE '^fix|^bug|^patch|^hotfix|^correct'; then
    category="Fixed"
  elif echo "$msg_lower" | grep -qE '^remove|^drop|^delete|^deprecate'; then
    category="Removed"
  fi
  SECTIONS["$category"]+="- $msg"$'\n'
done < <(git log "$LAST_TAG"..HEAD --oneline 2>/dev/null || echo "")

for section in "Added" "Changed" "Fixed" "Removed"; do
  if [ -n "${SECTIONS[$section]}" ]; then
    echo "### $section" >> "$CHANGELOG_FILE"
    echo "" >> "$CHANGELOG_FILE"
    echo -n "${SECTIONS[$section]}" >> "$CHANGELOG_FILE"
    echo "" >> "$CHANGELOG_FILE"
  fi
done

echo "Generated $CHANGELOG_FILE"
