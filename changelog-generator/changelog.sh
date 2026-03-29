#!/bin/bash
# changelog.sh - Generate a structured CHANGELOG.md from git history
# Automatically categorizes commits into Added/Fixed/Changed/Removed sections
# Usage: ./changelog.sh [--since TAG] [--output FILE]

set -euo pipefail

# Defaults
OUTPUT="CHANGELOG.md"
SINCE_TAG=""

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE_TAG="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: ./changelog.sh [--since TAG] [--output FILE]"
            echo "  --since TAG   Generate changelog since this tag (default: last tag)"
            echo "  --output FILE Output file (default: CHANGELOG.md)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Get the last tag if not specified
if [ -z "$SINCE_TAG" ]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Get current version info
CURRENT_DATE=$(date +%Y-%m-%d)
REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo "project")")

# Build commit range
if [ -n "$SINCE_TAG" ]; then
    RANGE="${SINCE_TAG}..HEAD"
    VERSION_LABEL="Unreleased (since ${SINCE_TAG})"
else
    RANGE=""
    VERSION_LABEL="All Changes"
fi

# Get commits
if [ -n "$RANGE" ]; then
    COMMITS=$(git log "$RANGE" --pretty=format:"%s|||%h|||%an" 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%s|||%h|||%an" 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
    echo "No commits found."
    exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    
    MSG=$(echo "$line" | cut -d'|||' -f1)
    HASH=$(echo "$line" | sed 's/.*|||//; s/|||.*//')
    
    # Lowercase for matching
    MSG_LOWER=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')
    
    # Categorize based on conventional commit prefixes and keywords
    if echo "$MSG_LOWER" | grep -qE "^(feat|add|new|create|implement|introduce)"; then
        ADDED="${ADDED}\n- ${MSG}"
    elif echo "$MSG_LOWER" | grep -qE "^(fix|bug|patch|resolve|repair|correct)"; then
        FIXED="${FIXED}\n- ${MSG}"
    elif echo "$MSG_LOWER" | grep -qE "^(remove|delete|drop|deprecat|clean)"; then
        REMOVED="${REMOVED}\n- ${MSG}"
    elif echo "$MSG_LOWER" | grep -qE "^(refactor|update|change|improve|enhance|bump|upgrade|modify|rename|move|migrate|optimi)"; then
        CHANGED="${CHANGED}\n- ${MSG}"
    elif echo "$MSG_LOWER" | grep -qE "(add|new|creat|implement|introduc)"; then
        ADDED="${ADDED}\n- ${MSG}"
    elif echo "$MSG_LOWER" | grep -qE "(fix|bug|patch|resolv|repair|correct)"; then
        FIXED="${FIXED}\n- ${MSG}"
    elif echo "$MSG_LOWER" | grep -qE "(remov|delet|drop|deprecat)"; then
        REMOVED="${REMOVED}\n- ${MSG}"
    elif echo "$MSG_LOWER" | grep -qE "(refactor|updat|chang|improv|enhanc|modif|renam|migrat|optimi)"; then
        CHANGED="${CHANGED}\n- ${MSG}"
    else
        OTHER="${OTHER}\n- ${MSG}"
    fi
done <<< "$COMMITS"

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "## ${VERSION_LABEL} Ã¢â¬â ${CURRENT_DATE}"
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

echo "Ã¢Åâ¦ CHANGELOG generated: ${OUTPUT}"
echo "   Version: ${VERSION_LABEL}"
TOTAL=$(echo "$COMMITS" | wc -l)
echo "   Total commits: ${TOTAL}"
