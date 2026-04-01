#!/bin/bash
# Generate structured CHANGELOG from git history
# Usage: ./generate-changelog.sh [since_tag]

SINCE="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "")}"

if [ -z "$SINCE" ]; then
    SINCE_LOG=$(git log --oneline --no-merges)
else
    SINCE_LOG=$(git log --oneline --no-merges "$SINCE..HEAD")
fi

echo "# Changelog"
echo ""
echo "Generated: $(date -u '+%Y-%m-%d %H:%M UTC')"
if [ -n "$SINCE" ]; then
    echo "Since: $SINCE"
fi
echo ""

# Categorize commits
FEATURES=""
FIXES=""
CHORES=""
BREAKING=""

while IFS= read -r line; do
    hash=$(echo "$line" | cut -d' ' -f1)
    msg=$(echo "$line" | cut -d' ' -f2-)

    case "$msg" in
        feat:*|feature:*|add:*)
            FEATURES="${FEATURES}\n- ${msg} (${hash})"
            ;;
        fix:*|bugfix:*|hotfix:*)
            FIXES="${FIXES}\n- ${msg} (${hash})"
            ;;
        BREAKING*|!:*)
            BREAKING="${BREAKING}\n- ${msg} (${hash})"
            ;;
        chore:*|refactor:*|docs:*|style:*|test:*|ci:*)
            CHORES="${CHORES}\n- ${msg} (${hash})"
            ;;
        *)
            FEATURES="${FEATURES}\n- ${msg} (${hash})"
            ;;
    esac
done <<< "$SINCE_LOG"

if [ -n "$BREAKING" ]; then
    echo "## Breaking Changes"
    echo -e "$BREAKING"
    echo ""
fi

if [ -n "$FEATURES" ]; then
    echo "## Features"
    echo -e "$FEATURES"
    echo ""
fi

if [ -n "$FIXES" ]; then
    echo "## Fixes"
    echo -e "$FIXES"
    echo ""
fi

if [ -n "$CHORES" ]; then
    echo "## Chores"
    echo -e "$CHORES"
    echo ""
fi
