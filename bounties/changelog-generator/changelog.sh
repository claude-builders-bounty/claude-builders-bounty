#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
# Default output: CHANGELOG.md

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

# Ensure we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: not in a git repository" >&2
    exit 1
fi

# Get the last tag, or use initial commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -z "$LAST_TAG" ]; then
    RANGE="HEAD"
    NEW_VERSION="0.1.0"
    echo "No tags found. Generating changelog from all commits."
else
    RANGE="${LAST_TAG}..HEAD"
    # Increment patch version from last tag
    NEW_VERSION=$(echo "$LAST_TAG" | awk -F. -v OFS='.' '{$NF++;print}')
    echo "Generating changelog from ${LAST_TAG} to HEAD."
fi

# Get commit data
COMMITS=$(git log --no-merges --pretty=format:"%H||%s" "$RANGE" 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
    echo "No new commits found since last tag."
    echo "## [${NEW_VERSION}] - $(date +%Y-%m-%d)" > "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "No changes." >> "$OUTPUT"
    exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    if [[ -z "$line" ]]; then continue; fi
    
    HASH="${line:0:40}"
    MSG="${line:42}"
    
    # Normalize message for matching
    MSG_LOWER=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')
    
    SHORT_HASH=$(echo "$HASH" | cut -c1-7)
    
    if echo "$MSG_LOWER" | grep -qE '^feat:|^add|^feature|^new'; then
        ADDED="${ADDED}- ${MSG} (${SHORT_HASH})\n"
    elif echo "$MSG_LOWER" | grep -qE '^fix:|^bug|^hotfix|^patch'; then
        FIXED="${FIXED}- ${MSG} (${SHORT_HASH})\n"
    elif echo "$MSG_LOWER" | grep -qE '^remove|^delete|^drop|^deprecate'; then
        REMOVED="${REMOVED}- ${MSG} (${SHORT_HASH})\n"
    else
        CHANGED="${CHANGED}- ${MSG} (${SHORT_HASH})\n"
    fi
done <<< "$COMMITS"

# Write CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "## [${NEW_VERSION}] - $(date +%Y-%m-%d)"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo -e "$ADDED" | while IFS= read -r l; do [ -n "$l" ] && echo "$l"; done
        echo ""
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo -e "$FIXED" | while IFS= read -r l; do [ -n "$l" ] && echo "$l"; done
        echo ""
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo -e "$CHANGED" | while IFS= read -r l; do [ -n "$l" ] && echo "$l"; done
        echo ""
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo -e "$REMOVED" | while IFS= read -r l; do [ -n "$l" ] && echo "$l"; done
        echo ""
    fi
} > "$OUTPUT"

echo "✅ Changelog generated at ${OUTPUT}"
echo "   Version: ${NEW_VERSION}"
