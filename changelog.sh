#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
#
set -euo pipefail

# --- Config ---
SINCE_TAG="${1:-}"
REPO_DIR="${2:-.}"
OUTPUT="${3:-CHANGELOG.md}"

cd "$REPO_DIR"

# Determine the range
if [ -n "$SINCE_TAG" ]; then
  RANGE="$SINCE_TAG..HEAD"
else
  # Find the latest tag
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [ -n "$LATEST_TAG" ]; then
    RANGE="$LATEST_TAG..HEAD"
  else
    RANGE="HEAD"
  fi
fi

# Collect commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
  msg=$(echo "$line" | sed 's/^[a-f0-9]* //')
  
  # Categorize by conventional commit prefix
  if echo "$msg" | grep -qiE '^(feat|add|new|create)\b'; then
    ADDED="${ADDED}- ${msg}"$'\n'
  elif echo "$msg" | grep -qiE '^(fix|bug|patch|hotfix|repair)\b'; then
    FIXED="${FIXED}- ${msg}"$'\n'
  elif echo "$msg" | grep -qiE '^(change|update|modify|refactor|improve|enhance|bump)\b'; then
    CHANGED="${CHANGED}- ${msg}"$'\n'
  elif echo "$msg" | grep -qiE '^(remove|delete|drop|deprecate|strip)\b'; then
    REMOVED="${REMOVED}- ${msg}"$'\n'
  else
    OTHER="${OTHER}- ${msg}"$'\n'
  fi
done < <(git log "$RANGE" --pretty=format:"%h %s" 2>/dev/null)

# Build CHANGELOG
TODAY=$(date +%Y-%m-%d)
HEADER="## [Unreleased] - ${TODAY}"

if [ -n "$SINCE_TAG" ] || [ -n "$LATEST_TAG" ]; then
  TAG_NAME="${SINCE_TAG:-$LATEST_TAG}"
  HEADER="## [$(git describe --tags --abbrev=0 HEAD 2>/dev/null || echo 'Unreleased')] - ${TODAY}"
fi

cat > "$OUTPUT" << HEADER
# Changelog

All notable changes to this project will be documented in this file.

${HEADER}
HEADER

[ -n "$ADDED" ]   && echo -e "### Added\n${ADDED}"   >> "$OUTPUT"
[ -n "$FIXED" ]   && echo -e "### Fixed\n${FIXED}"   >> "$OUTPUT"
[ -n "$CHANGED" ] && echo -e "### Changed\n${CHANGED}" >> "$OUTPUT"
[ -n "$REMOVED" ] && echo -e "### Removed\n${REMOVED}" >> "$OUTPUT"
[ -n "$OTHER" ]   && echo -e "### Other\n${OTHER}"   >> "$OUTPUT"

# Append old changelog if it exists
if [ -f CHANGELOG.old.md ]; then
  echo "" >> "$OUTPUT"
  cat CHANGELOG.old.md >> "$OUTPUT"
fi

echo "✅ Generated ${OUTPUT} (${RANGE})"
echo "   Added: $(echo -n "$ADDED" | grep -c '^-' || echo 0)"
echo "   Fixed: $(echo -n "$FIXED" | grep -c '^-' || echo 0)"
echo "   Changed: $(echo -n "$CHANGED" | grep -c '^-' || echo 0)"
echo "   Removed: $(echo -n "$REMOVED" | grep -c '^-' || echo 0)"
