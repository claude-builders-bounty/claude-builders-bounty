#!/bin/bash

# CHANGELOG Generator - Auto-generate CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]

OUTPUT_FILE="${1:-CHANGELOG.md}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

echo "# Changelog" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "All notable changes to this project will be documented in this file." >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"%H|%s|%b" --reverse)
else
    COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%H|%s|%b" --reverse)
fi

# Initialize category arrays
declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED

# Parse commits and categorize
while IFS='|' read -r HASH SUBJECT BODY; do
    if [ -z "$SUBJECT" ]; then
        continue
    fi
    
    # Categorize based on commit message prefix
    if [[ "$SUBJECT" =~ ^feat|^add ]]; then
        ADDED+=("- $SUBJECT")
    elif [[ "$SUBJECT" =~ ^fix|^bugfix ]]; then
        FIXED+=("- $SUBJECT")
    elif [[ "$SUBJECT" =~ ^refactor|^perf|^style ]]; then
        CHANGED+=("- $SUBJECT")
    elif [[ "$SUBJECT" =~ ^remove|^delete ]]; then
        REMOVED+=("- $SUBJECT")
    else
        CHANGED+=("- $SUBJECT")
    fi
done <<< "$COMMITS"

# Write sections to CHANGELOG
VERSION=$(date +%Y.%m.%d)
echo "## [$VERSION] - $(date +%Y-%m-%d)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added" >> "$OUTPUT_FILE"
    for item in "${ADDED[@]}"; do
        echo "$item" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed" >> "$OUTPUT_FILE"
    for item in "${FIXED[@]}"; do
        echo "$item" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed" >> "$OUTPUT_FILE"
    for item in "${CHANGED[@]}"; do
        echo "$item" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed" >> "$OUTPUT_FILE"
    for item in "${REMOVED[@]}"; do
        echo "$item" >> "$OUTPUT_FILE"
    done
    echo "" >> "$OUTPUT_FILE"
fi

echo "✅ CHANGELOG generated: $OUTPUT_FILE"
