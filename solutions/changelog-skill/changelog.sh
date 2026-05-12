#!/bin/bash
# changelog.sh - Auto-generate structured CHANGELOG.md from git history
# Usage: ./changelog.sh [since_tag]
#   - If no tag specified, uses the most recent tag
#   - If no tags exist, uses all commits

set -e

OUTPUT="CHANGELOG.md"
REPO=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "project")

# Determine starting point
if [ -n "$1" ]; then
    SINCE="$1"
else
    SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -z "$SINCE" ]; then
    RANGE=""
    HEADER_TAG="Initial"
else
    RANGE="$SINCE..HEAD"
    HEADER_TAG="$SINCE"
fi

# Get current date & version
DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "unreleased")

# Collect categorized commits
ADDED=$(git log $RANGE --no-merges --pretty=format:"- %s" --grep="^feat\|^add\|Add\|[Ff]eature" 2>/dev/null || echo "")
FIXED=$(git log $RANGE --no-merges --pretty=format:"- %s" --grep="^fix\|^bug\|[Ff]ix\|[Bb]ug" 2>/dev/null || echo "")
CHANGED=$(git log $RANGE --no-merges --pretty=format:"- %s" --grep="^refactor\|^perf\|^style\|[Rr]efactor\|[Uu]pdate\|[Ii]mprove" 2>/dev/null || echo "")
REMOVED=$(git log $RANGE --no-merges --pretty=format:"- %s" --grep="^remove\|^delete\|^revert\|[Rr]emove\|[Dd]elete" 2>/dev/null || echo "")

# Fallback: uncategorized commits
if [ -z "$ADDED$FIXED$CHANGED$REMOVED" ]; then
    ALL_COMMITS=$(git log $RANGE --no-merges --oneline 2>/dev/null | sed 's/^/- /' || echo "")
fi

# Build CHANGELOG
cat > "$OUTPUT" << EOF
# Changelog — $REPO

## [$VERSION] — $DATE
EOF

if [ -n "$ADDED" ]; then
    echo "" >> "$OUTPUT"
    echo "### Added" >> "$OUTPUT"
    echo "$ADDED" >> "$OUTPUT"
fi

if [ -n "$FIXED" ]; then
    echo "" >> "$OUTPUT"
    echo "### Fixed" >> "$OUTPUT"
    echo "$FIXED" >> "$OUTPUT"
fi

if [ -n "$CHANGED" ]; then
    echo "" >> "$OUTPUT"
    echo "### Changed" >> "$OUTPUT"
    echo "$CHANGED" >> "$OUTPUT"
fi

if [ -n "$REMOVED" ]; then
    echo "" >> "$OUTPUT"
    echo "### Removed" >> "$OUTPUT"
    echo "$REMOVED" >> "$OUTPUT"
fi

if [ -n "$ALL_COMMITS" ]; then
    echo "" >> "$OUTPUT"
    echo "### Changes" >> "$OUTPUT"
    echo "$ALL_COMMITS" >> "$OUTPUT"
fi

echo "✅ CHANGELOG.md generated (since $HEADER_TAG)"
echo "   Version: $VERSION | Date: $DATE"
