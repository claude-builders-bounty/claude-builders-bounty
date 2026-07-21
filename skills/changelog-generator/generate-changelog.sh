#!/bin/bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo "# Changelog" > "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "Initial release — no tags found." >> "$OUTPUT"
    exit 0
fi

{
    echo "# Changelog"
    echo ""
    echo "## [$(git describe --tags --abbrev=0)] - $(date +%Y-%m-%d)"
    echo ""

    declare -A CATEGORIES=(
        ["Added"]="feat|feature|add|implement"
        ["Fixed"]="fix|bugfix|hotfix|patch"
        ["Changed"]="refactor|update|upgrade|bump|migrate|redesign"
        ["Removed"]="remove|deprecate|drop|delete"
        ["Documentation"]="doc|readme|docs"
        ["Security"]="security|vuln|cve"
        ["Performance"]="perf|performance|optimize|speed"
    )

    for CAT in "Added" "Fixed" "Changed" "Removed" "Documentation" "Security" "Performance"; do
        PATTERN="${CATEGORIES[$CAT]}"
        COMMITS=$(git log "$LAST_TAG..HEAD" --pretty=format:"%s" --grep="$PATTERN" -i 2>/dev/null || true)
        if [ -n "$COMMITS" ]; then
            echo "### $CAT"
            echo "$COMMITS" | while IFS= read -r line; do
                echo "  - $line"
            done
            echo ""
        fi
    done

    UNCATEGORIZED=$(git log "$LAST_TAG..HEAD" --pretty=format:"%s" 2>/dev/null | grep -viE "$(IFS='|'; echo "${CATEGORIES[*]}")" || true)
    if [ -n "$UNCATEGORIZED" ]; then
        echo "### Uncategorized"
        echo "$UNCATEGORIZED" | while IFS= read -r line; do
            echo "  - $line"
        done
        echo ""
    fi
} > "$OUTPUT"

echo "Changelog generated: $OUTPUT"
