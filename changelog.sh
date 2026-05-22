#!/bin/bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# v1.0.0

set -euo pipefail

TAG="${1:-}"
OUT="CHANGELOG.md"

# Get commits since last tag, or all commits if no tag
if [ -z "$TAG" ]; then
    TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -n "$TAG" ]; then
    COMMITS=$(git log "${TAG}..HEAD" --pretty=format:"%s (%h)" --no-merges)
else
    COMMITS=$(git log --pretty=format:"%s (%h)" --no-merges)
fi

if [ -z "$COMMITS" ]; then
    echo "No new commits since ${TAG:-beginning}."
    exit 0
fi

# Categorize
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    msg=$(echo "$line" | sed 's/ (.*//')
    hash=$(echo "$line" | grep -oE '\([a-f0-9]+\)$' || true)
    
    lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    if echo "$lower" | grep -qE '^(feat|add|introduce|new|implement)'; then
        ADDED="${ADDED}- ${msg} ${hash}\n"
    elif echo "$lower" | grep -qE '^(fix|bug|close|solve|patch|correct|repair)'; then
        FIXED="${FIXED}- ${msg} ${hash}\n"
    elif echo "$lower" | grep -qE '^(remove|delete|drop|cleanup|clean)'; then
        REMOVED="${REMOVED}- ${msg} ${hash}\n"
    else
        CHANGED="${CHANGED}- ${msg} ${hash}\n"
    fi
done <<< "$COMMITS"

# Write CHANGELOG.md
{
echo "# Changelog"
echo ""
echo "All notable changes to this project will be documented in this file."
echo ""

if [ -n "$ADDED" ]; then
    echo "## Added"
    echo -e "$ADDED"
    echo ""
fi

if [ -n "$FIXED" ]; then
    echo "## Fixed"
    echo -e "$FIXED"
    echo ""
fi

if [ -n "$CHANGED" ]; then
    echo "## Changed"
    echo -e "$CHANGED"
    echo ""
fi

if [ -n "$REMOVED" ]; then
    echo "## Removed"
    echo -e "$REMOVED"
    echo ""
fi
} > "$OUT"

echo "✓ Generated $OUT"
cat "$OUT"
