#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
# Dependencies: git (that's it)

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

# Get the last tag, or use root commit if no tags
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
TAG_DATE=$(git log -1 --format=%ai "$LAST_TAG" 2>/dev/null | cut -d' ' -f1)
CURRENT_DATE=$(date +%Y-%m-%d)

# Get commits since last tag
COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%s" 2>/dev/null || git log --pretty=format:"%s")

if [ -z "$COMMITS" ]; then
    echo "No new commits since last tag ($LAST_TAG). Nothing to generate."
    exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r msg; do
    # Normalize: lowercase first word for matching
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    case "$lower_msg" in
        feat:*|feat\(*|add:*|add\(*|added:*)
            clean=$(echo "$msg" | sed 's/^[^:]*: *//')
            ADDED="${ADDED}\n  - ${clean}"
            ;;
        fix:*|fix\(*|bugfix:*|hotfix:*|fixed:*)
            clean=$(echo "$msg" | sed 's/^[^:]*: *//')
            FIXED="${FIXED}\n  - ${clean}"
            ;;
        refactor:*|refactor\(*|change:*|update:*|improve:*|perf:*|style:*)
            clean=$(echo "$msg" | sed 's/^[^:]*: *//')
            CHANGED="${CHANGED}\n  - ${clean}"
            ;;
        remove:*|delete:*|deprecate:*|removed:*|deprecated:*)
            clean=$(echo "$msg" | sed 's/^[^:]*: *//')
            REMOVED="${REMOVED}\n  - ${clean}"
            ;;
        *)
            # Try to infer from keywords in the message
            if echo "$lower_msg" | grep -qE "^(add|implement|create|introduce|new) "; then
                ADDED="${ADDED}\n  - ${msg}"
            elif echo "$lower_msg" | grep -qE "^(fix|resolve|patch|correct) "; then
                FIXED="${FIXED}\n  - ${msg}"
            elif echo "$lower_msg" | grep -qE "^(update|change|modify|refactor|improve|optimize) "; then
                CHANGED="${CHANGED}\n  - ${msg}"
            elif echo "$lower_msg" | grep -qE "^(remove|delete|drop|deprecate) "; then
                REMOVED="${REMOVED}\n  - ${msg}"
            else
                OTHER="${OTHER}\n  - ${msg}"
            fi
            ;;
    esac
done <<< "$COMMITS"

# Build output
{
    echo "# Changelog"
    echo ""
    echo "## [Unreleased] — $CURRENT_DATE"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo -e "$ADDED"
        echo ""
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo -e "$FIXED"
        echo ""
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo -e "$CHANGED"
        echo ""
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo -e "$REMOVED"
        echo ""
    fi
    
    if [ -n "$OTHER" ]; then
        echo "### Other"
        echo -e "$OTHER"
        echo ""
    fi
} > "$OUTPUT"

echo "✅ Generated $OUTPUT ($(wc -l < "$OUTPUT") lines)"
echo "   Commits processed: $(echo "$COMMITS" | wc -l)"
