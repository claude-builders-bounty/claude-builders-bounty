#!/bin/bash
set -e

# Find the last tag, or fallback to the first commit if no tags exist
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
if [ -z "$LAST_TAG" ]; then
    echo "Error: Not a git repository or no commits found."
    exit 1
fi

echo "Generating CHANGELOG from commits since: $LAST_TAG"

# Temporary files for categories
TMP_ADDED=$(mktemp)
TMP_FIXED=$(mktemp)
TMP_CHANGED=$(mktemp)
TMP_REMOVED=$(mktemp)

# Parse commits
git log ${LAST_TAG}..HEAD --pretty=format:"%s (%h)" | while read -r line; do
    # Simple conventional commit matching
    if echo "$line" | grep -iqE "^(feat|feature|add):"; then
        echo "- $(echo "$line" | sed -E 's/^(feat|feature|add)(\([^)]+\))?: //i')" >> "$TMP_ADDED"
    elif echo "$line" | grep -iqE "^(fix|bug):"; then
        echo "- $(echo "$line" | sed -E 's/^(fix|bug)(\([^)]+\))?: //i')" >> "$TMP_FIXED"
    elif echo "$line" | grep -iqE "^(remove|delete|rm):"; then
        echo "- $(echo "$line" | sed -E 's/^(remove|delete|rm)(\([^)]+\))?: //i')" >> "$TMP_REMOVED"
    elif echo "$line" | grep -iqE "^(refactor|style|chore|docs|test):"; then
        echo "- $(echo "$line" | sed -E 's/^(refactor|style|chore|docs|test)(\([^)]+\))?: //i')" >> "$TMP_CHANGED"
    else
        # Catch-all
        echo "- $line" >> "$TMP_CHANGED"
    fi
done

# Build CHANGELOG.md
OUTPUT="CHANGELOG.md"
echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## [Unreleased] - $(date +%Y-%m-%d)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

if [ -s "$TMP_ADDED" ]; then
    echo "### Added" >> "$OUTPUT"
    cat "$TMP_ADDED" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

if [ -s "$TMP_FIXED" ]; then
    echo "### Fixed" >> "$OUTPUT"
    cat "$TMP_FIXED" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

if [ -s "$TMP_CHANGED" ]; then
    echo "### Changed" >> "$OUTPUT"
    cat "$TMP_CHANGED" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

if [ -s "$TMP_REMOVED" ]; then
    echo "### Removed" >> "$OUTPUT"
    cat "$TMP_REMOVED" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

# Cleanup
rm "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED"

echo "Success! Output written to $OUTPUT"
