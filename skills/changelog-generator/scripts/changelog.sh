#!/usr/bin/env bash
# changelog.sh - Generate structured CHANGELOG.md from git history
# Part of Claude Builders Bounty #1 ($50)

set -euo pipefail

PROJECT_ROOT="${1:-.}"
cd "$PROJECT_ROOT"

OUTPUT="${2:-CHANGELOG.md}"

# Get last tag, or first commit if no tags exist
if LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
    RANGE="${LAST_TAG}..HEAD"
else
    FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD 2>/dev/null)
    RANGE="${FIRST_COMMIT}..HEAD"
fi

# Collect commits since last tag
COMMITS=$(git log "$RANGE" --pretty=format:"%h %s" 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    echo "No new commits since $LAST_TAG"
    exit 0
fi

# Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

# Parse commits
while IFS= read -r line; do
    if [ -z "$line" ]; then continue; fi
    
    hash=$(echo "$line" | cut -d' ' -f1)
    message=$(echo "$line" | cut -d' ' -f2-)
    
    # Categorize by Conventional Commit prefix
    case "$message" in
        feat:*|feature:*)
            ADDED="$ADDED
- $message"
            ;;
        fix:*|bugfix:*|hotfix:*)
            FIXED="$FIXED
- $message"
            ;;
        refactor:*|style:*|perf:*)
            CHANGED="$CHANGED
- $message"
            ;;
        revert:*|remove:*)
            REMOVED="$REMOVED
- $message"
            ;;
        chore:*|docs:*|test:*|ci:*|build:*)
            CHANGED="$CHANGED
- $message"
            ;;
        *)
            OTHER="$OTHER
- $message"
            ;;
    esac
done <<< "$COMMITS"

# Get current date and version tag
CURRENT_DATE=$(date +%Y-%m-%d)
VERSION_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")

# Generate changelog
{
    echo "# Changelog"
    echo ""
    
    # Check if file exists, prepend if so
    if [ -f "$OUTPUT" ]; then
        # Keep everything after first # Changelog heading
        EXISTING=$(sed '1,/^# Changelog/d' "$OUTPUT" 2>/dev/null || echo "")
    fi
    
    echo "## [$VERSION_TAG] - $CURRENT_DATE"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo -e "$ADDED" | sed '/^$/d'
        echo ""
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo -e "$FIXED" | sed '/^$/d'
        echo ""
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo -e "$CHANGED" | sed '/^$/d'
        echo ""
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo -e "$REMOVED" | sed '/^$/d'
        echo ""
    fi
    
    if [ -n "$OTHER" ]; then
        echo "### Other"
        echo -e "$OTHER" | sed '/^$/d'
        echo ""
    fi
    
} > "$OUTPUT"

COMMIT_COUNT=$(echo "$COMMITS" | wc -l | tr -d ' ')
echo "Generated $OUTPUT with $COMMIT_COUNT commits from $RANGE"
