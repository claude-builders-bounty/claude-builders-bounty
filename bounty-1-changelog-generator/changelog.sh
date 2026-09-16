#!/bin/bash

# Enable case-insensitive regex matching
shopt -s nocasematch

# Find the last git tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Generating changelog for all commits..."
    COMMITS=$(git log --pretty=format:"%s" 2>/dev/null)
else
    echo "Generating changelog for commits since tag: $LAST_TAG"
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s" 2>/dev/null)
fi

# Initialize arrays for categories
declare -a ADDED FIXED CHANGED REMOVED OTHER

if [ -n "$COMMITS" ]; then
    while IFS= read -r line; do
        if [[ "$line" =~ ^(feat|add|added|feature)(:| |\() ]]; then
            ADDED+=("- $line")
        elif [[ "$line" =~ ^(fix|fixed|bug)(:| |\() ]]; then
            FIXED+=("- $line")
        elif [[ "$line" =~ ^(change|changed|update|refactor|chore|docs|style|test)(:| |\() ]]; then
            CHANGED+=("- $line")
        elif [[ "$line" =~ ^(remove|removed|delete)(:| |\() ]]; then
            REMOVED+=("- $line")
        elif [ -n "$line" ]; then
            OTHER+=("- $line")
        fi
    done <<< "$COMMITS"
fi

OUTPUT="CHANGELOG.md"
DATE=$(date +%Y-%m-%d)

echo "# Changelog" > $OUTPUT
echo "" >> $OUTPUT
echo "## [Latest] - $DATE" >> $OUTPUT

if [ ${#ADDED[@]} -gt 0 ]; then
    echo "" >> $OUTPUT
    echo "### Added" >> $OUTPUT
    printf '%s\n' "${ADDED[@]}" >> $OUTPUT
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    echo "" >> $OUTPUT
    echo "### Fixed" >> $OUTPUT
    printf '%s\n' "${FIXED[@]}" >> $OUTPUT
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "" >> $OUTPUT
    echo "### Changed" >> $OUTPUT
    printf '%s\n' "${CHANGED[@]}" >> $OUTPUT
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "" >> $OUTPUT
    echo "### Removed" >> $OUTPUT
    printf '%s\n' "${REMOVED[@]}" >> $OUTPUT
fi

if [ ${#OTHER[@]} -gt 0 ]; then
    echo "" >> $OUTPUT
    echo "### Other" >> $OUTPUT
    printf '%s\n' "${OTHER[@]}" >> $OUTPUT
fi

echo "CHANGELOG.md has been generated successfully!"
