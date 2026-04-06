#!/usr/bin/env bash
set -euo pipefail

# CHANGELOG Generator
# Generates a structured CHANGELOG.md from git history since the last tag

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Get the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo -e "${YELLOW}No tags found. Generating changelog from all commits...${NC}"
    COMMIT_RANGE=""
else
    echo -e "${GREEN}Last tag: $LAST_TAG${NC}"
    COMMIT_RANGE="$LAST_TAG..HEAD"
fi

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Get commits
if [ -z "$COMMIT_RANGE" ]; then
    COMMITS=$(git log --pretty=format:"%s" --reverse)
else
    COMMITS=$(git log $COMMIT_RANGE --pretty=format:"%s" --reverse)
fi

# Check if there are new commits
if [ -z "$COMMITS" ]; then
    echo -e "${YELLOW}No new commits since last tag.${NC}"
    exit 0
fi

# Initialize categories as strings (easier than arrays for this use case)
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

# Categorize commits
while IFS= read -r commit; do
    # Convert to lowercase for matching
    commit_lower=$(echo "$commit" | tr '[:upper:]' '[:lower:]')
    
    # Match patterns and append to respective category
    if [[ "$commit_lower" =~ ^(add|feat|feature|new|create|implement) ]]; then
        ADDED+="- $commit\n"
    elif [[ "$commit_lower" =~ ^(fix|bugfix|patch|resolve|hotfix) ]]; then
        FIXED+="- $commit\n"
    elif [[ "$commit_lower" =~ ^(change|update|modify|refactor|improve|enhance|chore) ]]; then
        CHANGED+="- $commit\n"
    elif [[ "$commit_lower" =~ ^(remove|delete|drop) ]]; then
        REMOVED+="- $commit\n"
    else
        OTHER+="- $commit\n"
    fi
done <<< "$COMMITS"

# Generate CHANGELOG content
CHANGELOG_CONTENT="# CHANGELOG\n\n"

# Determine version header
if [ -z "$LAST_TAG" ]; then
    CHANGELOG_CONTENT+="## [Unreleased] - $CURRENT_DATE\n\n"
else
    CHANGELOG_CONTENT+="## [Unreleased] - $CURRENT_DATE\n\n"
    CHANGELOG_CONTENT+="_Changes since ${LAST_TAG}_\n\n"
fi

# Add categories (only if not empty)
if [ -n "$ADDED" ]; then
    CHANGELOG_CONTENT+="### Added\n$ADDED\n"
fi

if [ -n "$FIXED" ]; then
    CHANGELOG_CONTENT+="### Fixed\n$FIXED\n"
fi

if [ -n "$CHANGED" ]; then
    CHANGELOG_CONTENT+="### Changed\n$CHANGED\n"
fi

if [ -n "$REMOVED" ]; then
    CHANGELOG_CONTENT+="### Removed\n$REMOVED\n"
fi

if [ -n "$OTHER" ]; then
    CHANGELOG_CONTENT+="### Other\n$OTHER\n"
fi

# Write to CHANGELOG.md
echo -e "$CHANGELOG_CONTENT" > CHANGELOG.md

echo -e "${GREEN}✓ CHANGELOG.md generated successfully!${NC}"
echo -e "\n${YELLOW}Preview:${NC}"
echo -e "---"
cat CHANGELOG.md