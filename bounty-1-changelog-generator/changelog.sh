#!/usr/bin/env bash
# Automatically generates a structured CHANGELOG.md from git history
# Categories: Added, Fixed, Changed, Removed

set -e

# Find the last git tag, ignore errors if no tags exist
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --format="%s" 2>/dev/null || true)
    HEADER="## Initial Release"
else
    COMMITS=$(git log ${LAST_TAG}..HEAD --format="%s" 2>/dev/null || true)
    HEADER="## Changes since ${LAST_TAG}"
fi

if [ -z "$COMMITS" ]; then
    echo "No commits found to generate changelog."
    exit 0
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# Loop through commits and categorize
while IFS= read -r msg; do
    # Skip empty lines
    if [ -z "$msg" ]; then
        continue
    fi

    # Convert to lowercase for easier matching
    LOWER_MSG=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    # Categorization logic based on conventional commits and keywords
    if [[ "$LOWER_MSG" =~ ^(feat|add|new|create|implement) ]]; then
        ADDED="${ADDED}- ${msg}\n"
    elif [[ "$LOWER_MSG" =~ ^(fix|bug|patch|resolve) ]]; then
        FIXED="${FIXED}- ${msg}\n"
    elif [[ "$LOWER_MSG" =~ ^(remove|delete|drop|rm|clean) ]]; then
        REMOVED="${REMOVED}- ${msg}\n"
    else
        CHANGED="${CHANGED}- ${msg}\n"
    fi
done <<< "$COMMITS"

OUT="# Changelog\n\n$HEADER\n"

if [ -n "$ADDED" ]; then
    OUT="${OUT}\n### Added\n${ADDED}"
fi
if [ -n "$FIXED" ]; then
    OUT="${OUT}\n### Fixed\n${FIXED}"
fi
if [ -n "$CHANGED" ]; then
    OUT="${OUT}\n### Changed\n${CHANGED}"
fi
if [ -n "$REMOVED" ]; then
    OUT="${OUT}\n### Removed\n${REMOVED}"
fi

printf "%b\n" "$OUT" > CHANGELOG.md
echo "✅ CHANGELOG.md generated successfully!"
cat CHANGELOG.md
