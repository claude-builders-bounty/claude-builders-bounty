#!/bin/bash

# Changelog Generator
# Generates a structured CHANGELOG.md based on git history since the last tag.

# Configuration
OUTPUT_FILE="CHANGELOG.md"

# Find the most recent tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    echo "No git tags found. Generating changelog from first commit."
    RANGE="origin/main..HEAD" # Fallback range
else
    echo "Generating changelog since tag: $LAST_TAG"
    RANGE="$LAST_TAG..HEAD"
fi

# Fetch commits in the range
COMMITS=$(git log "$RANGE" --pretty=format:"%s")

if [ -z "$COMMITS" ]; then
    echo "No new commits found since $LAST_TAG."
    exit 0
fi

# Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# Categorize commits
while IFS= read -r line; do
    case "$line" in
        *feat*|*add*|*new*)
            ADDED+="- $line\n"
            ;;
        *fix*|*bug*|*patch*)
            FIXED+="- $line\n"
            ;;
        *refactor*|*update*|*change*)
            CHANGED+="- $line\n"
            ;;
        *remove*|*deprecate*|*delete*)
            REMOVED+="- $line\n"
            ;;
        *)
            CHANGED+="- $line\n"
            ;;
    esac
done <<< "$COMMITS"

# Build the changelog content
CONTENT="## [$(date +'%Y-%m-%d')] \n\n"

if [ -n "$ADDED" ]; then
    CONTENT+="### Added\n$ADDED\n"
fi

if [ -n "$FIXED" ]; then
    CONTENT+="### Fixed\n$FIXED\n"
fi

if [ -n "$CHANGED" ]; then
    CONTENT+="### Changed\n$CHANGED\n"
fi

if [ -n "$REMOVED" ]; then
    CONTENT+="### Removed\n$REMOVED\n"
fi

# Write to file
echo -e "$CONTENT" > "$OUTPUT_FILE"
echo "Successfully generated $OUTPUT_FILE"
