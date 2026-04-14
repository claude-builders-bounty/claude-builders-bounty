#!/usr/bin/env bash
# generate-changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [--since-tag TAG] [--output FILE]

set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE_TAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --since-tag) SINCE_TAG="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Find the last tag if not specified
if [[ -z "$SINCE_TAG" ]]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Build git log range
if [[ -n "$SINCE_TAG" ]]; then
    RANGE="${SINCE_TAG}..HEAD"
    echo "# Changelog (since ${SINCE_TAG})" > "$OUTPUT"
else
    RANGE="HEAD"
    echo "# Changelog" > "$OUTPUT"
fi

echo "" >> "$OUTPUT"
echo "Generated: $(date -u +%Y-%m-%d)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Categorize commits
declare -A CATEGORIES
CATEGORIES=(
    ["Added"]="^feat(\(|:|\s)"
    ["Fixed"]="^fix(\(|:|\s)"
    ["Changed"]="^refactor(\(|:||change|update|modify|improve)"
    ["Removed"]="^remove|^delete|deprecat"
)

# Also catch non-conventional commits
for category in "Added" "Fixed" "Changed" "Removed"; do
    pattern="${CATEGORIES[$category]}"
    commits=$(git log ${RANGE} --pretty=format:"- %s (%h)" --grep="$pattern" -i 2>/dev/null || true)
    if [[ -n "$commits" ]]; then
        echo "## ${category}" >> "$OUTPUT"
        echo "$commits" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
done

# Uncategorized commits
all_categorized=$(git log ${RANGE} --pretty=format:"%h" --grep="^feat\|^fix\|^refactor\|^remove\|^delete\|deprecat" -i 2>/dev/null || true)
uncategorized=$(git log ${RANGE} --pretty=format:"- %s (%h)" 2>/dev/null || true)

# Filter out already categorized
if [[ -n "$uncategorized" ]]; then
    echo "## Other Changes" >> "$OUTPUT"
    echo "$uncategorized" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

echo "✅ Changelog written to ${OUTPUT}"
