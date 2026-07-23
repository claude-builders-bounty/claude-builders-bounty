#!/bin/bash
set -euo pipefail

REPO_DIR="${1:-.}"
OUTPUT="${2:-CHANGELOG.md}"

cd "$REPO_DIR"

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
  COMMITS=$(git log --oneline --no-merges)
  RANGE="all commits"
else
  COMMITS=$(git log --oneline --no-merges "${LAST_TAG}..HEAD")
  RANGE="${LAST_TAG}..HEAD"
fi

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "> Generated on $(date '+%Y-%m-%d') from $RANGE" >> "$OUTPUT"
echo "" >> "$OUTPUT"

ADDED=""; FIXED=""; CHANGED=""; REMOVED=""

while IFS= read -r line; do
  [ -z "$line" ] && continue
  msg=$(echo "$line" | cut -d' ' -f2-)
  hash=$(echo "$line" | cut -d' ' -f1)

  if echo "$msg" | grep -qiE "^(feat|add|new|implement)"; then
    ADDED+="- $msg (${hash:0:7})\n"
  elif echo "$msg" | grep -qiE "^(fix|bug|patch|resolve|hotfix)"; then
    FIXED+="- $msg (${hash:0:7})\n"
  elif echo "$msg" | grep -qiE "^(remove|delete|drop|deprecate)"; then
    REMOVED+="- $msg (${hash:0:7})\n"
  else
    CHANGED+="- $msg (${hash:0:7})\n"
  fi
done <<< "$COMMITS"

[ -n "$ADDED" ] && { echo "## Added" >> "$OUTPUT"; echo "" >> "$OUTPUT"; printf "%b" "$ADDED" >> "$OUTPUT"; echo "" >> "$OUTPUT"; }
[ -n "$FIXED" ] && { echo "## Fixed" >> "$OUTPUT"; echo "" >> "$OUTPUT"; printf "%b" "$FIXED" >> "$OUTPUT"; echo "" >> "$OUTPUT"; }
[ -n "$CHANGED" ] && { echo "## Changed" >> "$OUTPUT"; echo "" >> "$OUTPUT"; printf "%b" "$CHANGED" >> "$OUTPUT"; echo "" >> "$OUTPUT"; }
[ -n "$REMOVED" ] && { echo "## Removed" >> "$OUTPUT"; echo "" >> "$OUTPUT"; printf "%b" "$REMOVED" >> "$OUTPUT"; echo "" >> "$OUTPUT"; }

echo "✅ CHANGELOG.md generated ($(echo "$COMMITS" | wc -l | tr -d ' ') commits from $RANGE)"
