#!/usr/bin/env bash
# changelog.sh - Generate structured CHANGELOG.md from git history
# Usage: ./changelog.sh [output_file]
# Default output: ./CHANGELOG.md
#
# Features:
#   - Categorizes commits using Conventional Commits (feat/fix/refactor/etc)
#   - Falls back to keyword-based categorization for non-conventional commits
#   - Generates Keep-a-Changelog format with version + date
#   - Zero dependencies (pure bash + git)
#   - Handles repos with no tags (uses full history)

set -eo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
PROJECT_NAME=$(basename "$(pwd)")

# Get last tag, or empty if no tags
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    RANGE=""
    LAST_TAG_NOTE="(full history)"
else
    RANGE="${LAST_TAG}..HEAD"
    LAST_TAG_NOTE="${LAST_TAG}"
fi

# Fetch commits with conventional commit messages
COMMITS=$(git log ${RANGE} --pretty=format:"%H|%s|%b" --no-merges 2>/dev/null)

if [ -z "$COMMITS" ]; then
    echo "Error: No commits found in range." >&2
    exit 1
fi

# Categorize commits into temp files
ADDED=$(mktemp)
FIXED=$(mktemp)
CHANGED=$(mktemp)
REMOVED=$(mktemp)
OTHER=$(mktemp)
trap "rm -f $ADDED $FIXED $CHANGED $REMOVED $OTHER" EXIT

# Helper function: extract message after prefix
extract_msg() {
    local subject="$1"
    local prefix="$2"
    if [[ "$subject" == "$prefix:"* ]]; then
        echo "${subject#${prefix}: }"
        return 0
    elif [[ "$subject" == "${prefix}("* ]]; then
        # Has scope like feat(scope):
        local rest="${subject#${prefix}(}"
        local scope="${rest%%)*}"
        local msg="${rest#*): }"
        echo "$msg"
        return 0
    fi
    return 1
}

while IFS='|' read -r hash subject body; do
    [ -z "$subject" ] && continue

    SHORT_HASH=$(echo "$hash" | cut -c1-7)
    CATEGORY=""

    # Try conventional commit prefixes
    if MSG=$(extract_msg "$subject" "feat"); then
        CATEGORY="$ADDED"
    elif MSG=$(extract_msg "$subject" "fix"); then
        CATEGORY="$FIXED"
    elif MSG=$(extract_msg "$subject" "refactor"); then
        CATEGORY="$CHANGED"
    elif MSG=$(extract_msg "$subject" "perf"); then
        CATEGORY="$CHANGED"
    elif MSG=$(extract_msg "$subject" "style"); then
        CATEGORY="$CHANGED"
    elif MSG=$(extract_msg "$subject" "chore"); then
        CATEGORY="$CHANGED"
    elif MSG=$(extract_msg "$subject" "docs"); then
        CATEGORY="$CHANGED"
    elif MSG=$(extract_msg "$subject" "build"); then
        CATEGORY="$CHANGED"
    elif MSG=$(extract_msg "$subject" "ci"); then
        CATEGORY="$CHANGED"
    elif MSG=$(extract_msg "$subject" "remove"); then
        CATEGORY="$REMOVED"
    elif MSG=$(extract_msg "$subject" "delete"); then
        CATEGORY="$REMOVED"
    elif MSG=$(extract_msg "$subject" "drop"); then
        CATEGORY="$REMOVED"
    elif MSG=$(extract_msg "$subject" "deprecate"); then
        CATEGORY="$REMOVED"
    fi

    if [ -n "$CATEGORY" ]; then
        echo "- ${MSG} (${SHORT_HASH})" >> "$CATEGORY"
        continue
    fi

    # No conventional prefix - categorize by keywords
    LOWER=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    if [[ "$LOWER" =~ (^|[^a-z])(add|new|create|implement|introduce)([^a-z]|$) ]]; then
        echo "- ${subject} (${SHORT_HASH})" >> "$ADDED"
    elif [[ "$LOWER" =~ (^|[^a-z])(fix|bug|patch|repair|resolve|correct)([^a-z]|$) ]]; then
        echo "- ${subject} (${SHORT_HASH})" >> "$FIXED"
    elif [[ "$LOWER" =~ (^|[^a-z])(remove|delete|drop|deprecate|eliminate)([^a-z]|$) ]]; then
        echo "- ${subject} (${SHORT_HASH})" >> "$REMOVED"
    else
        echo "- ${subject} (${SHORT_HASH})" >> "$OTHER"
    fi
done <<< "$COMMITS"

# Determine version
VERSION=$(date +"%Y.%m.%d")
if [ -f "package.json" ]; then
    PKG_VERSION=$(grep -m1 '"version"' package.json 2>/dev/null | sed 's/.*"version": *"\([^"]*\)".*/\1/')
    [ -n "$PKG_VERSION" ] && VERSION="$PKG_VERSION"
fi
if [ -f "VERSION" ]; then
    FILE_VERSION=$(cat VERSION 2>/dev/null | tr -d '[:space:]')
    [ -n "$FILE_VERSION" ] && VERSION="$FILE_VERSION"
fi

RELEASE_DATE=$(date -u +"%Y-%m-%d")
COMMIT_COUNT=$(echo "$COMMITS" | wc -l)

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to **${PROJECT_NAME}** are documented here."
    echo ""
    echo "Format based on [Keep a Changelog](https://keepachangelog.com/)."
    echo ""
    echo "---"
    echo ""
    echo "## [${VERSION}] - ${RELEASE_DATE}"
    echo ""
    echo "_Commits since ${LAST_TAG_NOTE} (${COMMIT_COUNT} total)_"
    echo ""

    for category_file in "Added:$ADDED" "Fixed:$FIXED" "Changed:$CHANGED" "Removed:$REMOVED"; do
        CATEGORY="${category_file%:*}"
        FILE="${category_file#*:}"
        if [ -s "$FILE" ]; then
            echo "### ${CATEGORY}"
            echo ""
            cat "$FILE"
            echo ""
        fi
    done

    if [ -s "$OTHER" ]; then
        echo "### Other"
        echo ""
        cat "$OTHER"
        echo ""
    fi

    echo "---"
    echo ""
    echo "_Generated on $(date -u +"%Y-%m-%dT%H:%M:%SZ") by changelog.sh_"
} > "$OUTPUT_FILE"

echo "Generated ${OUTPUT_FILE} (${COMMIT_COUNT} commits since ${LAST_TAG_NOTE})" >&2
