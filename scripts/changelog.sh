#!/bin/bash
# changelog.sh - Generate a structured CHANGELOG.md from git history
#
# Usage: bash changelog.sh [OUTPUT_FILE]
# Default output: CHANGELOG.md
#
# Requirements: Git repository with at least one tag

set -e

OUTPUT="${1:-CHANGELOG.md}"

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}📝 Generating changelog...${NC}"

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Get the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo -e "${YELLOW}No tags found. Using all commits.${NC}"
    COMMITS=$(git log --pretty=format:"%s" --no-merges)
else
    echo -e "${GREEN}Found last tag: ${LAST_TAG}${NC}"
    COMMITS=$(git log "${LAST_TAG}"..HEAD --pretty=format:"%s" --no-merges)
fi

# Initialize arrays for each category
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

# Categorize commits
while IFS= read -r line; do
    [ -z "$line" ] && continue

    # Remove leading/trailing whitespace
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    # Categorize based on prefix
    case "$line" in
        feat:*|feature:*|add:*)
            ADDED+=("$line")
            ;;
        fix:*|bugfix:*|hotfix:*)
            FIXED+=("$line")
            ;;
        change:*|refactor:*|update:*|improve:*|style:*)
            CHANGED+=("$line")
            ;;
        remove:*|deprecate:*|delete:*)
            REMOVED+=("$line")
            ;;
        docs:*|chore:*|test:*|ci:*|build:*|perf:*)
            OTHER+=("$line")
            ;;
        *)
            OTHER+=("$line")
            ;;
    esac
done <<< "$COMMITS"

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "## [Unreleased]"
    echo ""

    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        for item in "${ADDED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        for item in "${FIXED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        for item in "${CHANGED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        for item in "${REMOVED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    if [ ${#OTHER[@]} -gt 0 ]; then
        echo "### Other"
        for item in "${OTHER[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    # Add footer with generation info
    echo "---"
    echo "*Generated on $(date '+%Y-%m-%d %H:%M:%S')*"
    if [ -n "$LAST_TAG" ]; then
        echo "*Since tag: $LAST_TAG*"
    fi
} > "$OUTPUT"

# Summary
TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]}))
echo -e "${GREEN}✅ Generated ${NC}${YELLOW}$OUTPUT${NC}${GREEN} with $TOTAL commits${NC}"
echo -e "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]} | Other: ${#OTHER[@]}"