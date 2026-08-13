#!/bin/bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]

set -euo pipefail

OUTPUT=${1:-CHANGELOG.md}
TEMP_FILE=$(mktemp)

# Get the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Using all commits."
    COMMITS=$(git log --oneline --no-merges)
else
    echo "Fetching commits since $LAST_TAG"
    COMMITS=$(git log ${LAST_TAG}..HEAD --oneline --no-merges)
fi

if [ -z "$COMMITS" ]; then
    echo "No commits found."
    exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
    # Extract commit message (remove hash)
    MSG=$(echo "$line" | sed 's/^[a-f0-9]* //')
    
    # Categorize based on conventional commit prefixes
    case "$MSG" in
        feat:*|add:*|added:*|new:*)
            ADDED="$ADDED
- $MSG"
            ;;
        fix:*|fixed:*|bugfix:*|patch:*)
            FIXED="$FIXED
- $MSG"
            ;;
        refactor:*|change:*|changed:*|update:*|updated:*|improve:*|improved:*)
            CHANGED="$CHANGED
- $MSG"
            ;;
        remove:*|removed:*|delete:*|deleted:*)
            REMOVED="$REMOVED
- $MSG"
            ;;
        *)
            OTHER="$OTHER
- $MSG"
            ;;
    esac
done <<< "$COMMITS"

# Build CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "Generated on $(date +%Y-%m-%d)"
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
    
    if [ -n "$OTHER" ]; then
        echo "## Other"
        echo -e "$OTHER"
        echo ""
    fi
} > "$OUTPUT"

echo "CHANGELOG.md generated successfully!"
echo "Found $(echo "$COMMITS" | wc -l) commits."
