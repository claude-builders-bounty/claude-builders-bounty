#!/bin/bash

# changelog.sh - Automatically generate a structured CHANGELOG.md from git history
# Categories: Added, Fixed, Changed, Removed

set -e

# Find the latest tag. If none exists, get the first commit.
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LATEST_TAG" ]; then
    # No tags, use the root commit
    REVISION_RANGE="HEAD"
    PREVIOUS_VERSION="Initial Commit"
else
    REVISION_RANGE="${LATEST_TAG}..HEAD"
    PREVIOUS_VERSION="${LATEST_TAG}"
fi

# Output file
OUTPUT="CHANGELOG.md"

# Collect commits
COMMITS=$(git log $REVISION_RANGE --pretty=format:"%s|%h|%an")

declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED

# Parse commits
while IFS='|' read -r subject hash author; do
    # Skip empty lines
    [ -z "$subject" ] && continue

    prefix=$(echo "$subject" | cut -d':' -f1 | tr '[:upper:]' '[:lower:]')
    message=$(echo "$subject" | cut -d':' -f2- | sed -e 's/^[[:space:]]*//')

    case "$prefix" in
        *feat*|*add*)
            ADDED+=("- $message ($hash) by $author")
            ;;
        *fix*|*bug*)
            FIXED+=("- $message ($hash) by $author")
            ;;
        *remove*|*del*|*drop*)
            REMOVED+=("- $message ($hash) by $author")
            ;;
        *)
            # Fallback for chore, refactor, style, docs, etc.
            CHANGED+=("- $subject ($hash) by $author")
            ;;
    esac
done <<< "$COMMITS"

# Write to CHANGELOG.md
echo "# Changelog" > $OUTPUT
echo "" >> $OUTPUT
echo "Changes since $PREVIOUS_VERSION" >> $OUTPUT

write_section() {
    local title=$1
    shift
    local items=("$@")

    if [ ${#items[@]} -gt 0 ]; then
        echo "" >> $OUTPUT
        echo "## $title" >> $OUTPUT
        for item in "${items[@]}"; do
            echo "$item" >> $OUTPUT
        done
    fi
}

write_section "Added" "${ADDED[@]}"
write_section "Fixed" "${FIXED[@]}"
write_section "Changed" "${CHANGED[@]}"
write_section "Removed" "${REMOVED[@]}"

echo "" >> $OUTPUT
echo "Changelog successfully generated at $OUTPUT"
