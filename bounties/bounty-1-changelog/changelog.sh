#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [output_file]
#   output_file defaults to CHANGELOG.md

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
DATE=$(date +%Y-%m-%d)

# Get commits since last tag (or all commits if no tag)
if [ -n "$TAG" ]; then
    RANGE="${TAG}..HEAD"
    HEADER="## [$TAG] → Unreleased — $DATE"
else
    RANGE="HEAD"
    HEADER="## [Initial Release] — $DATE"
fi

# Collect commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    
    # Extract conventional commit type and message
    if [[ "$line" =~ ^feat(\(.+\))?!?:\ (.+) ]]; then
        ADDED="${ADDED}\n- ${BASH_REMATCH[2]}"
    elif [[ "$line" =~ ^fix(\(.+\))?!?:\ (.+) ]]; then
        FIXED="${FIXED}\n- ${BASH_REMATCH[2]}"
    elif [[ "$line" =~ ^(chore|refactor|perf|style)(\(.+\))?!?:\ (.+) ]]; then
        CHANGED="${CHANGED}\n- ${BASH_REMATCH[3]}"
    elif [[ "$line" =~ ^remove(\(.+\))?!?:\ (.+) ]] || [[ "$line" =~ ^delete(\(.+\))?!?:\ (.+) ]]; then
        REMOVED="${REMOVED}\n- ${BASH_REMATCH[2]}"
    elif [[ "$line" =~ ^docs(\(.+\))?!?:\ (.+) ]]; then
        CHANGED="${CHANGED}\n- ${BASH_REMATCH[2]}"
    elif [[ "$line" =~ ^build(\(.+\))?!?:\ (.+) ]]; then
        CHANGED="${CHANGED}\n- ${BASH_REMATCH[2]}"
    elif [[ "$line" =~ ^ci(\(.+\))?!?:\ (.+) ]]; then
        CHANGED="${CHANGED}\n- ${BASH_REMATCH[2]}"
    elif [[ "$line" =~ ^test(\(.+\))?!?:\ (.+) ]]; then
        CHANGED="${CHANGED}\n- ${BASH_REMATCH[2]}"
    else
        OTHER="${OTHER}\n- ${line}"
    fi
done < <(git log --format="%s" $RANGE 2>/dev/null || git log --format="%s")

# Build CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "$HEADER"
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
    
    # If no commits found
    if [ -z "$ADDED" ] && [ -z "$FIXED" ] && [ -z "$CHANGED" ] && [ -z "$REMOVED" ] && [ -z "$OTHER" ]; then
        echo "_No commits found in this range._"
        echo ""
    fi
    
} > "$OUTPUT"

echo "✅ Generated $OUTPUT"
