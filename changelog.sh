#!/usr/bin/env bash
set -euo pipefail

# generate-changelog
# Generates CHANGELOG.md from git history since last tag

OUTPUT_FILE="${1:-CHANGELOG.md}"

# Get tags sorted by version
TAGS=$(git tag --sort=-version:refname 2>/dev/null || true)

if [ -z "$TAGS" ]; then
    # No tags found — use all commits
    RANGES=("HEAD")
else
    # Build ranges from newest to oldest tag
    FIRST=true
    RANGES=()
    PREV=""
    for TAG in $TAGS; do
        if [ "$FIRST" = true ]; then
            RANGES+=("$TAG..HEAD")
            PREV="$TAG"
            FIRST=false
        else
            RANGES+=("$TAG..$PREV")
            PREV="$TAG"
        fi
    done
    RANGES+=("$PREV")
fi

generate_section() {
    local range="$1"
    local label="$2"

    # Get commits, extract the subject after the prefix
    COMMITS=$(git log "$range" --no-merges --pretty=format:"%s" 2>/dev/null | grep -E '^(feat|fix|refactor|chore|docs|style|perf|test|revert|security)(\(.+\))?:' || true)

    if [ -z "$COMMITS" ]; then
        # Fallback: use all commits, try to categorize by keyword
        COMMITS=$(git log "$range" --no-merges --pretty=format:"- %s" 2>/dev/null | head -50 || true)
    fi

    echo "$COMMITS"
}

categorize() {
    local range="$1"

    # Categories
    for CAT in "Added:feat" "Fixed:fix" "Changed:refactor chore docs style perf test" "Removed:revert" "Security:security"; do
        HEADER="${CAT%%:*}"
        PREFIXES="${CAT##*:}"

        for PREFIX in $PREFIXES; do
            git log "$range" --no-merges --pretty=format:"- %s" 2>/dev/null | grep -iE "^\- ${PREFIX}(\(.+\))?:" | sed 's/^\- '"${PREFIX}"'\(([^)]*)\)\?:\s*/- /I' || true
        done
    done
}

# Generate the changelog
{
    echo "# Changelog"
    echo ""

    for RANGE in "${RANGES[@]}"; do
        if echo "$RANGE" | grep -q '\.\.'; then
            TAG="${RANGE#*..}"
        else
            TAG="$RANGE"
        fi

        # Get tag date
        TAG_DATE=$(git log -1 --format="%ad" --date=short "$TAG" 2>/dev/null || date +%Y-%m-%d)
        TAG_NAME=$(echo "$TAG" | sed 's/^v//')

        echo "## [$TAG_NAME] - $TAG_DATE"
        echo ""

        categorize "$RANGE" | while IFS= read -r LINE; do
            echo "$LINE"
        done

        echo ""
    done

} > "$OUTPUT_FILE"

echo "✅ Generated $OUTPUT_FILE"
