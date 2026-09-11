#!/usr/bin/env bash
set -euo pipefail

# Git Changelog Generator
# Generates a categorized CHANGELOG.md from commits since the last tag

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
    echo "Generating changelog since tag: $LAST_TAG"
    RANGE="${LAST_TAG}..HEAD"
else
    echo "No prior tag found. Generating changelog for entire history."
    RANGE="HEAD"
fi

OUTPUT_FILE="CHANGELOG.md"
DATE=$(date +"%Y-%m-%d")

mkdir -p "$(dirname "$OUTPUT_FILE")"

TMP_ADDED=$(mktemp)
TMP_FIXED=$(mktemp)
TMP_CHANGED=$(mktemp)
TMP_REMOVED=$(mktemp)
TMP_OTHER=$(mktemp)

git log "$RANGE" --pretty=format:"%s (%h by %an)" | while IFS= read -r line; do
    case "$line" in
        feat:*|Feat:*|*feat:*|*add:*|*Add:*)
            echo "- ${line#*: }" >> "$TMP_ADDED"
            ;;
        fix:*|Fix:*|*fix:*|*bug:*|*Bug:*)
            echo "- ${line#*: }" >> "$TMP_FIXED"
            ;;
        refactor:*|style:*|perf:*|docs:*|chore:*)
            echo "- ${line#*: }" >> "$TMP_CHANGED"
            ;;
        revert:*|remove:*|deprecate:*)
            echo "- ${line#*: }" >> "$TMP_REMOVED"
            ;;
        *)
            echo "- $line" >> "$TMP_OTHER"
            ;;
    esac
done

{
    echo "# Changelog"
    echo ""
    echo "## [Unreleased] - $DATE"
    echo ""
    if [ -s "$TMP_ADDED" ]; then
        echo "### Added"
        cat "$TMP_ADDED"
        echo ""
    fi
    if [ -s "$TMP_FIXED" ]; then
        echo "### Fixed"
        cat "$TMP_FIXED"
        echo ""
    fi
    if [ -s "$TMP_CHANGED" ]; then
        echo "### Changed"
        cat "$TMP_CHANGED"
        echo ""
    fi
    if [ -s "$TMP_REMOVED" ]; then
        echo "### Removed"
        cat "$TMP_REMOVED"
        echo ""
    fi
    if [ -s "$TMP_OTHER" ]; then
        echo "### Other Changes"
        cat "$TMP_OTHER"
        echo ""
    fi
} > "$OUTPUT_FILE"

rm -f "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED" "$TMP_OTHER"

echo "Changelog generated successfully at $OUTPUT_FILE"
