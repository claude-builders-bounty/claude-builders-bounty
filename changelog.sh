#!/bin/bash

#generates a changelog.md from git history

#default file name
OUTPUT_FILE="CHANGELOG.md"

#get the last tag, if any
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Generating changelog from all commits."
    LOG_RANGE=""
else
    echo "Generating changelog since tag: $LAST_TAG"
    LOG_RANGE="${LAST_TAG}..HEAD"
fi

#arrays for categorized commits
declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED

#process each commit message
while read -r commit_msg; do
    #skip empty lines
    if [ -z "$commit_msg" ]; then continue; fi

    #lowercase the message for easier matching
    lower_msg=$(echo "$commit_msg" | tr '[:upper:]' '[:lower:]')

    #categorize based on keywords
    if [[ "$lower_msg" =~ ^-\ (feat|add|new) ]]; then
        ADDED+=("$commit_msg")
    elif [[ "$lower_msg" =~ ^-\ (fix|bug|patch) ]]; then
        FIXED+=("$commit_msg")
    elif [[ "$lower_msg" =~ ^-\ (remove|del|drop) ]]; then
        REMOVED+=("$commit_msg")
    else
        #default to changed for everything else (chore, docs, refactor, etc.)
        CHANGED+=("$commit_msg")
    fi
done < <(git log $LOG_RANGE --pretty=format:"- %s")

#write to changelog.md
echo "# Changelog" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

#add current date
echo "## [Unreleased] - $(date +%Y-%m-%d)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added" >> "$OUTPUT_FILE"
    for msg in "${ADDED[@]}"; do
        echo "$msg" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed" >> "$OUTPUT_FILE"
    for msg in "${FIXED[@]}"; do
        echo "$msg" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed" >> "$OUTPUT_FILE"
    for msg in "${CHANGED[@]}"; do
        echo "$msg" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed" >> "$OUTPUT_FILE"
    for msg in "${REMOVED[@]}"; do
        echo "$msg" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

echo "CHANGELOG.md generated successfully!"
