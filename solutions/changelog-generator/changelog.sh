#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since TAG] [--output FILE]
#
# Examples:
#   bash changelog.sh                    # Since last tag
#   bash changelog.sh --since v1.2.0     # Since specific tag
#   bash changelog.sh --output CHANGES   # Custom output file

set -euo pipefail

# Parse arguments
SINCE_TAG=""
OUTPUT="CHANGELOG.md"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE_TAG="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --help|-h) echo "Usage: bash changelog.sh [--since TAG] [--output FILE]"; exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Detect last tag if not specified
if [[ -z "$SINCE_TAG" ]]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -z "$SINCE_TAG" ]]; then
    echo "⚠️  No tags found. Generating changelog from all commits."
    RANGE="HEAD"
    HEADER="Unreleased"
else
    echo "📋 Generating changelog since $SINCE_TAG"
    RANGE="${SINCE_TAG}..HEAD"
    HEADER="Unreleased (since $SINCE_TAG)"
fi

# Get today's date
DATE=$(date +%Y-%m-%d)

# Collect commits
COMMITS=$(git log "$RANGE" --pretty=format:"%s	%h	%an" 2>/dev/null || git log --pretty=format:"%s	%h	%an")

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    MSG=$(echo "$line" | awk -F'\t' '{print $1}')
    HASH=$(echo "$line" | awk -F'\t' '{print $2}')
    AUTHOR=$(echo "$line" | awk -F'\t' '{print $3}')
    
    # Convert to lowercase for matching
    MSG_LOWER=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')
    
    ENTRY="- ${MSG} (\`${HASH}\`)"
    
    if echo "$MSG_LOWER" | grep -qE "^(feat|add|new|create|implement|introduce|support)"; then
        ADDED="${ADDED}\n${ENTRY}"
    elif echo "$MSG_LOWER" | grep -qE "^(fix|bug|patch|resolve|repair|correct|hotfix)"; then
        FIXED="${FIXED}\n${ENTRY}"
    elif echo "$MSG_LOWER" | grep -qE "^(remove|delete|deprecate|drop|prune)"; then
        REMOVED="${REMOVED}\n${ENTRY}"
    elif echo "$MSG_LOWER" | grep -qE "^(refactor|change|update|improve|enhance|optimize|perf|style|chore|ci|build|docs|test)"; then
        CHANGED="${CHANGED}\n${ENTRY}"
    else
        # Try content-based matching
        if echo "$MSG_LOWER" | grep -qE "(add|new|feature|implement|introduce)"; then
            ADDED="${ADDED}\n${ENTRY}"
        elif echo "$MSG_LOWER" | grep -qE "(fix|bug|issue|error|crash|resolve)"; then
            FIXED="${FIXED}\n${ENTRY}"
        elif echo "$MSG_LOWER" | grep -qE "(remov|delet|deprecat|drop)"; then
            REMOVED="${REMOVED}\n${ENTRY}"
        else
            CHANGED="${CHANGED}\n${ENTRY}"
        fi
    fi
done <<< "$COMMITS"

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
    echo ""
    echo "## [$HEADER] — $DATE"
    echo ""
    
    if [[ -n "$ADDED" ]]; then
        echo "### Added"
        echo -e "$ADDED"
        echo ""
    fi
    
    if [[ -n "$FIXED" ]]; then
        echo "### Fixed"
        echo -e "$FIXED"
        echo ""
    fi
    
    if [[ -n "$CHANGED" ]]; then
        echo "### Changed"
        echo -e "$CHANGED"
        echo ""
    fi
    
    if [[ -n "$REMOVED" ]]; then
        echo "### Removed"
        echo -e "$REMOVED"
        echo ""
    fi
} > "$OUTPUT"

# Count entries
TOTAL=$(echo -e "${ADDED}${FIXED}${CHANGED}${REMOVED}" | grep -c "^-" || true)
echo "✅ Generated $OUTPUT with $TOTAL entries"
echo ""
echo "Summary:"
[[ -n "$ADDED" ]] && echo "  Added:   $(echo -e "$ADDED" | grep -c "^-" || true)"
[[ -n "$FIXED" ]] && echo "  Fixed:   $(echo -e "$FIXED" | grep -c "^-" || true)"
[[ -n "$CHANGED" ]] && echo "  Changed: $(echo -e "$CHANGED" | grep -c "^-" || true)"
[[ -n "$REMOVED" ]] && echo "  Removed: $(echo -e "$REMOVED" | grep -c "^-" || true)"
