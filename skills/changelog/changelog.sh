#!/bin/bash

# CHANGELOG Generator
# Generates a structured CHANGELOG.md from git commit history
# Usage: bash changelog.sh

set -e

CHANGELOG_FILE="CHANGELOG.md"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📝 Generating CHANGELOG.md...${NC}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

# Get the last tag, or use the first commit if no tags
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

# Get commits since last tag
if [ "$LAST_TAG" = "$(git rev-list --max-parents=0 HEAD)" ]; then
    echo "No tags found. Including all commits."
    COMMITS=$(git log --pretty=format:"%H|%s|%ai" --reverse)
else
    echo "Commits since tag: $LAST_TAG"
    COMMITS=$(git log --pretty=format:"%H|%s|%ai" "$LAST_TAG"..HEAD --reverse)
fi

# Initialize arrays for each category
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

# Process each commit
while IFS='|' read -r hash message date; do
    # Skip empty lines
    [ -z "$hash" ] && continue
    
    # Extract commit type from message
    lower_message=$(echo "$message" | tr '[:upper:]' '[:lower:]')
    
    if echo "$lower_message" | grep -qE "^(feat|feature)[:(]"; then
        ADDED+=("- $message")
    elif echo "$lower_message" | grep -qE "^(fix|bugfix|hotfix)[:(]"; then
        FIXED+=("- $message")
    elif echo "$lower_message" | grep -qE "^(remove|delete|deprecate)[:(]"; then
        REMOVED+=("- $message")
    elif echo "$lower_message" | grep -qE "^(refactor|chore|docs|style|test|ci|build|perf)[:(]"; then
        CHANGED+=("- $message")
    else
        # If no conventional commit prefix, categorize as Changed
        CHANGED+=("- $message")
    fi
done <<< "$COMMITS"

# Generate date for the version
VERSION_DATE=$(date +%Y-%m-%d)

# Build the CHANGELOG content
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    echo ""
    echo "## [Unreleased] - $VERSION_DATE"
    echo ""
    
    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        echo ""
        printf '%s\n' "${ADDED[@]}"
        echo ""
    fi
    
    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        echo ""
        printf '%s\n' "${CHANGED[@]}"
        echo ""
    fi
    
    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        echo ""
        printf '%s\n' "${FIXED[@]}"
        echo ""
    fi
    
    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        echo ""
        printf '%s\n' "${REMOVED[@]}"
        echo ""
    fi
    
} > "$CHANGELOG_FILE"

echo -e "${GREEN}✅ CHANGELOG.md generated successfully!${NC}"
echo -e "${YELLOW}📊 Summary:${NC}"
echo "  - Added: ${#ADDED[@]} items"
echo "  - Changed: ${#CHANGED[@]} items"
echo "  - Fixed: ${#FIXED[@]} items"
echo "  - Removed: ${#REMOVED[@]} items"
echo ""
echo "File: $CHANGELOG_FILE"