#!/bin/bash

# changelog.sh - Automatically generate a structured CHANGELOG.md from git history

# Get the last git tag, if it exists
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    # If no tags exist, get all commits
    COMMITS=$(git log --pretty=format:"%s")
    TAG_STR="Initial commit to HEAD"
else
    # Get commits since the last tag
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s")
    TAG_STR="Commits since ${LAST_TAG}"
fi

# Arrays to hold categorized commits
declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED

# Read each commit and categorize
while IFS= read -r commit; do
    # Skip empty lines
    [ -z "$commit" ] && continue
    
    # Convert to lowercase for matching using standard bash
    lower_commit=$(echo "$commit" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lower_commit" == add* ]] || [[ "$lower_commit" == feat* ]]; then
        ADDED+=("- $commit")
    elif [[ "$lower_commit" == fix* ]] || [[ "$lower_commit" == patch* ]]; then
        FIXED+=("- $commit")
    elif [[ "$lower_commit" == rem* ]] || [[ "$lower_commit" == del* ]] || [[ "$lower_commit" == drop* ]]; then
        REMOVED+=("- $commit")
    else
        CHANGED+=("- $commit")
    fi
done <<< "$COMMITS"

# Generate CHANGELOG.md
OUTPUT_FILE="CHANGELOG.md"

echo "# CHANGELOG" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## Generated on $(date +'%Y-%m-%d') ($TAG_STR)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added" >> "$OUTPUT_FILE"
    printf '%s\n' "${ADDED[@]}" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed" >> "$OUTPUT_FILE"
    printf '%s\n' "${FIXED[@]}" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed" >> "$OUTPUT_FILE"
    printf '%s\n' "${CHANGED[@]}" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed" >> "$OUTPUT_FILE"
    printf '%s\n' "${REMOVED[@]}" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

echo "Successfully generated $OUTPUT_FILE!"
