#!/bin/bash

# CHANGELOG Generator from Git History
# For claude-builders-bounty Issue #1

set -e

# Configuration
OUTPUT_FILE="CHANGELOG.md"
INCLUDE_HASHES=true
INCLUDE_AUTHORS=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to categorize commit
categorize_commit() {
    local message="$1"
    local category=""
    
    # Convert to lowercase for matching
    local lower_msg=$(echo "$message" | tr '[:upper:]' '[:lower:]')
    
    # Added
    if echo "$lower_msg" | grep -qE '\b(add|new|feature|implement|create|introduce|support)\b'; then
        category="Added"
    # Fixed
    elif echo "$lower_msg" | grep -qE '\b(fix|bug|patch|resolve|correct|repair|issue)\b'; then
        category="Fixed"
    # Changed
    elif echo "$lower_msg" | grep -qE '\b(change|update|modify|improve|refactor|enhance|optimize|upgrade)\b'; then
        category="Changed"
    # Removed
    elif echo "$lower_msg" | grep -qE '\b(remove|delete|deprecate|drop|eliminate|clean)\b'; then
        category="Removed"
    # Default to Changed
    else
        category="Changed"
    fi
    
    echo "$category"
}

# Function to format commit message
format_commit() {
    local hash="$1"
    local message="$2"
    local author="$3"
    local result="- $message"
    
    if [ "$INCLUDE_HASHES" = true ]; then
        result="$result ($hash)"
    fi
    
    if [ "$INCLUDE_AUTHORS" = true ]; then
        result="$result by $author"
    fi
    
    echo "$result"
}

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Get latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LATEST_TAG" ]; then
    echo -e "${YELLOW}Warning: No tags found. Generating changelog for all commits.${NC}"
    COMMIT_RANGE="HEAD"
else
    echo -e "${GREEN}Found latest tag: $LATEST_TAG${NC}"
    COMMIT_RANGE="$LATEST_TAG..HEAD"
fi

# Get repository name
REPO_NAME=$(basename -s .git $(git config --get remote.origin.url 2>/dev/null || echo "project"))

# Initialize changelog content
CHANGELOG_CONTENT="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# If we have a tag, process commits since that tag
if [ -n "$LATEST_TAG" ]; then
    # Get tag date
    TAG_DATE=$(git log -1 --format=%ai $LATEST_TAG | cut -d' ' -f1)
    
    CHANGELOG_CONTENT+="## [$LATEST_TAG] - $CURRENT_DATE

"
fi

# Get all commits in range
COMMITS=$(git log $COMMIT_RANGE --pretty=format:"%H|%s|%an" --reverse 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    echo -e "${YELLOW}No commits found in range${NC}"
    exit 0
fi

# Initialize category arrays
declare -A categories
categories["Added"]=""
categories["Fixed"]=""
categories["Changed"]=""
categories["Removed"]=""

# Process each commit
while IFS='|' read -r hash message author; do
    # Skip empty lines
    [ -z "$hash" ] && continue
    
    # Skip merge commits
    if echo "$message" | grep -qE '^Merge (pull request|branch)'; then
        continue
    fi
    
    # Get short hash
    short_hash=$(echo "$hash" | cut -c1-7)
    
    # Categorize commit
    category=$(categorize_commit "$message")
    
    # Format commit
    formatted=$(format_commit "$short_hash" "$message" "$author")
    
    # Add to appropriate category
    categories[$category]+="$formatted
"
done <<< "$COMMITS"

# Build changelog sections
for cat in "Added" "Fixed" "Changed" "Removed"; do
    if [ -n "${categories[$cat]}" ]; then
        CHANGELOG_CONTENT+="### $cat
${categories[$cat]}
"
    fi
done

# If we have a previous tag, add reference
if [ -n "$LATEST_TAG" ]; then
    CHANGELOG_CONTENT+="[$LATEST_TAG]: https://github.com/user/repo/compare/v0.0.0...$LATEST_TAG
"
fi

# Write to file
echo "$CHANGELOG_CONTENT" > "$OUTPUT_FILE"

echo -e "${GREEN}✓ Changelog generated successfully: $OUTPUT_FILE${NC}"
echo -e "${GREEN}  Total commits processed: $(echo "$COMMITS" | wc -l)${NC}"

# Show preview
echo -e "\n${YELLOW}Preview:${NC}"
head -n 20 "$OUTPUT_FILE"

exit 0
