#!/bin/bash
# changelog.sh
# Generates a structured CHANGELOG.md from a project's git history since the last tag.

set -e

# File to output
OUTPUT_FILE="CHANGELOG.md"

# Get the last tag, suppress error if no tags exist
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Fetching all commits..."
    COMMITS=$(git log --pretty=format:"%h|%s")
else
    echo "Fetching commits since tag: $LAST_TAG..."
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%h|%s")
fi

# Arrays to hold categorized commits
declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED

# Read commits line by line
while IFS='|' read -r hash msg; do
    # Skip empty lines
    if [ -z "$hash" ]; then continue; fi
    
    # Convert message to lowercase for matching
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    # Categorization logic
    if [[ "$lower_msg" == add* || "$lower_msg" == feat* || "$lower_msg" == create* ]]; then
        ADDED+=("- $hash - $msg")
    elif [[ "$lower_msg" == fix* || "$lower_msg" == bug* || "$lower_msg" == patch* ]]; then
        FIXED+=("- $hash - $msg")
    elif [[ "$lower_msg" == remove* || "$lower_msg" == delete* || "$lower_msg" == drop* || "$lower_msg" == deprecate* ]]; then
        REMOVED+=("- $hash - $msg")
    else
        CHANGED+=("- $hash - $msg")
    fi
done <<< "$COMMITS"

# Generate CHANGELOG.md content
echo "# Changelog" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ -n "$LAST_TAG" ]; then
    echo "## Changes since tag: $LAST_TAG" >> "$OUTPUT_FILE"
else
    echo "## All Changes" >> "$OUTPUT_FILE"
fi

if [ ${#ADDED[@]} -gt 0 ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "### Added" >> "$OUTPUT_FILE"
    for item in "${ADDED[@]}"; do echo "$item" >> "$OUTPUT_FILE"; done
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "### Fixed" >> "$OUTPUT_FILE"
    for item in "${FIXED[@]}"; do echo "$item" >> "$OUTPUT_FILE"; done
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "### Changed" >> "$OUTPUT_FILE"
    for item in "${CHANGED[@]}"; do echo "$item" >> "$OUTPUT_FILE"; done
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "### Removed" >> "$OUTPUT_FILE"
    for item in "${REMOVED[@]}"; do echo "$item" >> "$OUTPUT_FILE"; done
fi

echo "✅ Successfully generated $OUTPUT_FILE!"
