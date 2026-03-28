#!/bin/bash

# CHANGELOG Generator - Generate structured CHANGELOG from git history
# Usage: ./changelog.sh [output_file]
# Default output: CHANGELOG.md

set -e

OUTPUT_FILE="${1:-CHANGELOG.md}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📝 Generating CHANGELOG from git history...${NC}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Check if repo has any commits
if ! git rev-parse HEAD > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Repository has no commits yet${NC}"
    # Create empty CHANGELOG
    cat > "$OUTPUT_FILE" << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

## [v0.1.0] - TBD

No changes recorded yet.
EOF
    echo -e "${GREEN}✅ Created empty CHANGELOG (no commits yet)${NC}"
    exit 0
fi

# Get the last tag (or use initial commit if no tags)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo -e "${YELLOW}No tags found, fetching all commits...${NC}"
    COMMITS=$(git log --pretty=format:"%s")
else
    echo -e "${GREEN}Fetching commits since tag: $LAST_TAG${NC}"
    COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%s" 2>/dev/null || git log --pretty=format:"%s")
fi

# Initialize arrays for categories
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Keywords for categorization
ADDED_KEYWORDS="add|create|implement|new|feat|feature|initial"
FIXED_KEYWORDS="fix|bug|patch|resolve|repair|correct"
CHANGED_KEYWORDS="change|update|modify|refactor|improve|enhance|style|docs|test"
REMOVED_KEYWORDS="remove|delete|drop|deprecate|eliminate"

# Categorize commits
while IFS= read -r commit; do
    [ -z "$commit" ] && continue
    
    commit_lower=$(echo "$commit" | tr '[:upper:]' '[:lower:]')
    
    if echo "$commit_lower" | grep -qE "$REMOVED_KEYWORDS"; then
        REMOVED+=("$commit")
    elif echo "$commit_lower" | grep -qE "$FIXED_KEYWORDS"; then
        FIXED+=("$commit")
    elif echo "$commit_lower" | grep -qE "$CHANGED_KEYWORDS"; then
        CHANGED+=("$commit")
    elif echo "$commit_lower" | grep -qE "$ADDED_KEYWORDS"; then
        ADDED+=("$commit")
    else
        # Default to Changed if no match
        CHANGED+=("$commit")
    fi
done <<< "$COMMITS"

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    
    CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")
    echo "## [$CURRENT_VERSION] - $(date +%Y-%m-%d)"
    echo ""
    
    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        for commit in "${ADDED[@]}"; do
            echo "- $commit"
        done
        echo ""
    fi
    
    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        for commit in "${FIXED[@]}"; do
            echo "- $commit"
        done
        echo ""
    fi
    
    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        for commit in "${CHANGED[@]}"; do
            echo "- $commit"
        done
        echo ""
    fi
    
    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        for commit in "${REMOVED[@]}"; do
            echo "- $commit"
        done
        echo ""
    fi
    
    if [ ${#ADDED[@]} -eq 0 ] && [ ${#FIXED[@]} -eq 0 ] && [ ${#CHANGED[@]} -eq 0 ] && [ ${#REMOVED[@]} -eq 0 ]; then
        echo "No changes recorded."
        echo ""
    fi
    
} > "$OUTPUT_FILE"

# Summary
TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]}))
echo -e "${GREEN}✅ Generated CHANGELOG with $TOTAL commits${NC}"
echo -e "${GREEN}📄 Output: $OUTPUT_FILE${NC}"

if [ ${#ADDED[@]} -gt 0 ]; then echo -e "   Added: ${#ADDED[@]}"; fi
if [ ${#FIXED[@]} -gt 0 ]; then echo -e "   Fixed: ${#FIXED[@]}"; fi
if [ ${#CHANGED[@]} -gt 0 ]; then echo -e "   Changed: ${#CHANGED[@]}"; fi
if [ ${#REMOVED[@]} -gt 0 ]; then echo -e "   Removed: ${#REMOVED[@]}"; fi
