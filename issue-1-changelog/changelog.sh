#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   ./changelog.sh                  # Generate from last tag to HEAD
#   ./changelog.sh v1.0.0..v2.0.0   # Generate for a specific range
#   ./changelog.sh --all            # Generate full history
#
# Categories: Added, Fixed, Changed, Removed
#

set -euo pipefail

RANGE=""
if [[ "${1:-}" == "--all" ]]; then
    RANGE=""
elif [[ -n "${1:-}" ]]; then
    RANGE="$1"
else
    # Default: from last tag to HEAD
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$LAST_TAG" ]]; then
        RANGE="${LAST_TAG}..HEAD"
    fi
fi

# Build commit log
if [[ -n "$RANGE" ]]; then
    COMMITS=$(git log "$RANGE" --pretty=format:"%s" 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%s" 2>/dev/null || echo "")
fi

if [[ -z "$COMMITS" ]]; then
    echo "No commits found for the specified range."
    exit 1
fi

# Date for the header
TODAY=$(date +%Y-%m-%d)

# Header
HEADER="# Changelog"
if [[ -n "$RANGE" ]]; then
    HEADER="${HEADER}\n\n## ${TODAY} (${RANGE})"
else
    HEADER="${HEADER}\n\n## ${TODAY}"
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r commit; do
    [[ -z "$commit" ]] && continue

    # Normalize: lowercase for matching
    lower=$(echo "$commit" | tr '[:upper:]' '[:lower:]')

    if echo "$lower" | grep -qE '^(add|feat|create|introduce|implement|support|new)'; then
        ADDED="${ADDED}- ${commit}\n"
    elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|repair|correct|hotfix)'; then
        FIXED="${FIXED}- ${commit}\n"
    elif echo "$lower" | grep -qE '^(remove|delete|drop|deprecate|strip|eliminate)'; then
        REMOVED="${REMOVED}- ${commit}\n"
    elif echo "$lower" | grep -qE '^(change|update|modify|refactor|rename|move|upgrade|migrate|bump|improve)'; then
        CHANGED="${CHANGED}- ${commit}\n"
    else
        # Default to Changed
        CHANGED="${CHANGED}- ${commit}\n"
    fi
done <<< "$COMMITS"

# Build output
OUTPUT="${HEADER}\n"

if [[ -n "$ADDED" ]]; then
    OUTPUT="${OUTPUT}\n### Added\n${ADDED}"
fi
if [[ -n "$FIXED" ]]; then
    OUTPUT="${OUTPUT}\n### Fixed\n${FIXED}"
fi
if [[ -n "$CHANGED" ]]; then
    OUTPUT="${OUTPUT}\n### Changed\n${CHANGED}"
fi
if [[ -n "$REMOVED" ]]; then
    OUTPUT="${OUTPUT}\n### Removed\n${REMOVED}"
fi

echo -e "$OUTPUT"
