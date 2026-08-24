#!/usr/bin/env bash

# Find latest tag or fall back to initial commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -n "$LAST_TAG" ]; then
    RANGE="$LAST_TAG..HEAD"
    HEADER_TITLE="## [Unreleased] - $(date +%Y-%m-%d) (since $LAST_TAG)"
else
    RANGE="HEAD"
    HEADER_TITLE="## [Unreleased] - $(date +%Y-%m-%d)"
fi

COMMITS=$(git log $RANGE --oneline 2>/dev/null)

if [ -z "$COMMITS" ]; then
    echo "No commits found to process."
    exit 0
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    MSG=$(echo "$line" | sed -E 's/^[a-f0-9]+ //')
    case "$MSG" in
        feat*|add*|New*)
            ADDED="${ADDED}- ${MSG}\n"
            ;;
        fix*|bug*)
            FIXED="${FIXED}- ${MSG}\n"
            ;;
        remove*|deprecate*)
            REMOVED="${REMOVED}- ${MSG}\n"
            ;;
        *)
            CHANGED="${CHANGED}- ${MSG}\n"
            ;;
    esac
done <<< "$COMMITS"

{
    echo "$HEADER_TITLE"
    echo ""
    if [ -n "$ADDED" ]; then
        echo "### Added"
        printf "$ADDED"
        echo ""
    fi
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        printf "$FIXED"
        echo ""
    fi
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        printf "$CHANGED"
        echo ""
    fi
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        printf "$REMOVED"
        echo ""
    fi
} > CHANGELOG.md

echo "CHANGELOG.md successfully generated."