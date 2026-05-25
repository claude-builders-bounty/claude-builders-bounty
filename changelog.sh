#!/bin/bash
# changelog.sh - Generate a structured CHANGELOG.md from git history
set -euo pipefail
OUTPUT="${1:-CHANGELOG.md}"
REPO_DIR="${2:-.}"
cd "$REPO_DIR"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
echo "Generating CHANGELOG from commits since: $LAST_TAG"
COMMITS=$(git log "$LAST_TAG"..HEAD --format="%s|||%b|||%H" --no-merges 2>/dev/null || echo "")
if [ -z "$COMMITS" ]; then
  echo "# Changelog" > "$OUTPUT"
  echo "" >> "$OUTPUT"
  echo "No changes since $LAST_TAG." >> "$OUTPUT"
  exit 0
fi
ADDED=""; FIXED=""; CHANGED=""; REMOVED=""
while IFS= read -r line; do
  [ -z "$line" ] && continue
  MSG="${line%%|||*}"; HASH="${line##*|||}"
  if echo "$MSG" | grep -qiE "^(feat|add|feature|new):"; then
    ADDED="$ADDED- $MSG (${HASH:0:7})\n"
  elif echo "$MSG" | grep -qiE "^(fix|bugfix|hotfix|bug):"; then
    FIXED="$FIXED- $MSG (${HASH:0:7})\n"
  elif echo "$MSG" | grep -qiE "^(remove|delete|drop|deprecate):"; then
    REMOVED="$REMOVED- $MSG (${HASH:0:7})\n"
  else
    CHANGED="$CHANGED- $MSG (${HASH:0:7})\n"
  fi
done <<< "$COMMITS"
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.1.0")
DATE=$(date +%Y-%m-%d)
{
  echo "# Changelog"; echo ""
  echo "## [$VERSION] - $DATE"; echo ""
  if [ -n "$ADDED" ]; then echo "### Added"; echo -e "$ADDED" | sed '/^$/d'; echo ""; fi
  if [ -n "$CHANGED" ]; then echo "### Changed"; echo -e "$CHANGED" | sed '/^$/d'; echo ""; fi
  if [ -n "$FIXED" ]; then echo "### Fixed"; echo -e "$FIXED" | sed '/^$/d'; echo ""; fi
  if [ -n "$REMOVED" ]; then echo "### Removed"; echo -e "$REMOVED" | sed '/^$/d'; echo ""; fi
} > "$OUTPUT"
echo "CHANGELOG generated at: $OUTPUT | Version: $VERSION | Date: $DATE"
