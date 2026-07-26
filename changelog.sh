#!/usr/bin/env bash
# CHANGELOG Generator — $50 bounty
# Generates structured CHANGELOG.md from git history since last tag

set -euo pipefail

OUTPUT="CHANGELOG.md"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"

if [ -z "$LAST_TAG" ]; then
    echo "## [Unreleased] — Initial Release" >> "$OUTPUT"
    COMMITS=$(git log --oneline --no-merges)
else
    VERSION=$(git describe --tags 2>/dev/null || echo "next")
    DATE=$(date +%Y-%m-%d)
    echo "## [$VERSION] — $DATE" >> "$OUTPUT"
    COMMITS=$(git log --oneline --no-merges "${LAST_TAG}..HEAD")
fi

echo "" >> "$OUTPUT"

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r commit; do
    MSG=$(echo "$commit" | cut -d' ' -f2-)
    
    if echo "$MSG" | grep -qiE "^(add|feat|new|create|implement)"; then
        ADDED+="  - $MSG"$'\n'
    elif echo "$MSG" | grep -qiE "^(fix|bug|resolve|patch|hotfix)"; then
        FIXED+="  - $MSG"$'\n'
    elif echo "$MSG" | grep -qiE "^(remove|delete|drop|deprecate)"; then
        REMOVED+="  - $MSG"$'\n'
    else
        CHANGED+="  - $MSG"$'\n'
    fi
done <<< "$COMMITS"

# Output sections
if [ -n "$ADDED" ]; then
    echo "### Added" >> "$OUTPUT"
    echo "$ADDED" >> "$OUTPUT"
fi

if [ -n "$FIXED" ]; then
    echo "### Fixed" >> "$OUTPUT"
    echo "$FIXED" >> "$OUTPUT"
fi

if [ -n "$CHANGED" ]; then
    echo "### Changed" >> "$OUTPUT"
    echo "$CHANGED" >> "$OUTPUT"
fi

if [ -n "$REMOVED" ]; then
    echo "### Removed" >> "$OUTPUT"
    echo "$REMOVED" >> "$OUTPUT"
fi

echo "✅ Generated $OUTPUT with $(echo "$COMMITS" | grep -c . || echo 0) commits"
