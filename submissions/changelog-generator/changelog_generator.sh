#!/bin/bash
# changelog_generator.sh — Generate CHANGELOG.md from git history

set -euo pipefail
OUTPUT="${1:-CHANGELOG.md}"

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Not a git repository"; exit 1
fi

TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
RANGE="${TAG:+${TAG}..}HEAD"

{
    echo "# Changelog"
    echo ""
    echo "## [${TAG:-Initial Release}] - $(date +%Y-%m-%d)"
    echo ""

    ALL=$(git log "$RANGE" --oneline 2>/dev/null || true)

    ADDED=$(echo "$ALL" | grep -iE "(feat|add|create|new|implement)" || true)
    FIXED=$(echo "$ALL" | grep -iE "(fix|bug|hotfix|patch|correct)" || true)
    CHANGED=$(echo "$ALL" | grep -iE "(change|update|refactor|improve|migrate)" || true)
    REMOVED=$(echo "$ALL" | grep -iE "(remove|delete|deprecat|drop)" || true)

    for section in "Added $ADDED" "Fixed $FIXED" "Changed $CHANGED" "Removed $REMOVED"; do
        name="${section%% *}"
        items="${section#* }"
        if [ -n "$items" ]; then
            echo "### $name"
            echo "$items" | while IFS= read -r line; do echo "- ${line#* }"; done
            echo ""
        fi
    done

    if [ -z "$ADDED$FIXED$CHANGED$REMOVED" ] && [ -n "$ALL" ]; then
        echo "### Changes"
        echo "$ALL" | while IFS= read -r line; do echo "- ${line#* }"; done
        echo ""
    fi
} > "$OUTPUT"

echo "Generated $OUTPUT"
