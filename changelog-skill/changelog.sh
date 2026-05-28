#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
#
# Fetches commits since the last git tag and categorizes them:
#   Added   — new features (feat:)
#   Fixed   — bug fixes (fix:)
#   Changed — refactors, docs, chores, perf, style
#   Removed — removals, deprecations (remove:, delete:, deprecate:)

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
DATE=$(date +%Y-%m-%d)

if [[ -n "$TAG" ]]; then
    RANGE="${TAG}..HEAD"
    HEADER="## [Unreleased] — ${DATE} (since ${TAG})"
else
    RANGE="HEAD"
    HEADER="## [Unreleased] — ${DATE}"
fi

# Get commits in reverse chronological order
COMMITS=$(git log "$RANGE" --pretty=format:"%s|%h" --no-merges 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
    echo "No commits found since ${TAG:-the beginning}."
    exit 0
fi

# Categorize commits
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

while IFS='|' read -r MSG HASH; do
    # Skip empty lines
    [[ -z "$MSG" ]] && continue

    # Normalize: lowercase for matching
    MSG_LOWER=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')
    ENTRY="- ${MSG} (\`${HASH}\`)"

    if [[ "$MSG_LOWER" =~ ^feat(\(.*\))?!?:\  ]]; then
        ADDED+=("$ENTRY")
    elif [[ "$MSG_LOWER" =~ ^fix(\(.*\))?!?:\  ]]; then
        FIXED+=("$ENTRY")
    elif [[ "$MSG_LOWER" =~ ^(remove|delete|deprecate)(\(.*\))?!?:\  ]]; then
        REMOVED+=("$ENTRY")
    elif [[ "$MSG_LOWER" =~ ^(refactor|perf|style|docs|chore|build|ci|test)(\(.*\))?!?:\  ]]; then
        CHANGED+=("$ENTRY")
    else
        # Treat uncategorized commits as Changed
        CHANGED+=("$ENTRY")
    fi
done <<< "$COMMITS"

# Build the changelog
{
    echo "# Changelog"
    echo ""
    echo "$HEADER"
    echo ""

    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        printf '%s\n' "${ADDED[@]}"
        echo ""
    fi

    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        printf '%s\n' "${FIXED[@]}"
        echo ""
    fi

    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        printf '%s\n' "${CHANGED[@]}"
        echo ""
    fi

    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        printf '%s\n' "${REMOVED[@]}"
        echo ""
    fi
} > "$OUTPUT_FILE"

echo "✅ Changelog generated: ${OUTPUT_FILE}"
echo "   Commits processed: $(echo "$COMMITS" | wc -l | tr -d ' ')"
echo "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]}"
