#!/bin/bash
# changelog.sh - Generate structured CHANGELOG.md from git history
# 
# Usage: ./changelog.sh [--output CHANGELOG.md] [--since-tag v1.0.0]
#
# Parses conventional commits (feat:, fix:, chore:, docs:, refactor:, etc.)
# and generates a categorized CHANGELOG.md

set -e

# Configuration
OUTPUT_FILE="${OUTPUT_FILE:-CHANGELOG.md}"
SINCE_TAG="${SINCE_TAG:-}"
REPO_URL="${REPO_URL:-$(git remote get-url origin 2>/dev/null || echo "")}"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --since-tag|-s)
            SINCE_TAG="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --output, -o FILE    Output file (default: CHANGELOG.md)"
            echo "  --since-tag, -s TAG Only include commits since this tag"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  OUTPUT_FILE          Output file path"
            echo "  SINCE_TAG            Git tag to start from"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Determine the starting point
if [ -z "$SINCE_TAG" ]; then
    # Get the latest tag, or use the first commit if no tags exist
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
fi

# Get current version info
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")
VERSION=${CURRENT_TAG#v}
DATE=$(date +%Y-%m-%d)

# Get commits since the tag
COMMITS=$(git log ${SINCE_TAG}..HEAD --pretty=format:"%h|%s|%an|%ad" --date=short 2>/dev/null || git log --pretty=format:"%h|%s|%an|%ad" --date=short)

if [ -z "$COMMITS" ]; then
    echo -e "${YELLOW}No commits found since ${SINCE_TAG}${NC}"
    exit 0
fi

# Function to get category from prefix
get_category() {
    local prefix="$1"
    case "$prefix" in
        feat|feature|add)
            echo "Added"
            ;;
        fix|bugfix|bug)
            echo "Fixed"
            ;;
        chore|refactor|change|update|style|perf|test|build|ci)
            echo "Changed"
            ;;
        remove|revert|deprecate)
            echo "Removed"
            ;;
        docs|doc)
            echo "Docs"
            ;;
        *)
            echo "Other"
            ;;
    esac
}

# Temporary files for categories
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

touch "$TEMP_DIR/Added"
touch "$TEMP_DIR/Fixed"
touch "$TEMP_DIR/Changed"
touch "$TEMP_DIR/Removed"
touch "$TEMP_DIR/Docs"
touch "$TEMP_DIR/Other"

# Process commits
while IFS='|' read -r hash message author date; do
    # Skip empty lines
    [ -z "$hash" ] && continue
    
    # Extract prefix (feat:, fix:, etc.)
    prefix=$(echo "$message" | grep -oE '^[a-zA-Z]+' | tr '[:upper:]' '[:lower:]')
    
    # Get category for prefix
    category=$(get_category "$prefix")
    
    # Format the commit line - remove prefix and clean up
    clean_message=$(echo "$message" | sed 's/^[^:]*://' | sed 's/^ *//' | sed 's/^ *//')
    
    # Skip if message becomes empty after cleaning
    [ -z "$clean_message" ] && continue
    
    # Add commit hash link if repo URL exists
    if [ -n "$REPO_URL" ]; then
        # Convert SSH URL to HTTPS if needed
        REPO_URL_HTTPS=$(echo "$REPO_URL" | sed 's|git@github.com:|https://github.com/|' | sed 's|\.git$||')
        commit_line="- $clean_message ([${hash}]($REPO_URL_HTTPS/commit/$hash))"
    else
        commit_line="- $clean_message ($hash)"
    fi
    
    echo "$commit_line" >> "$TEMP_DIR/$category"
done <<< "$COMMITS"

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    echo ""
    echo "---"
    echo ""
    echo "## [$VERSION] - $DATE"
    echo ""
    
    # Output each category if it has entries
    for category in "Added" "Fixed" "Changed" "Removed" "Docs"; do
        if [ -s "$TEMP_DIR/$category" ]; then
            echo "### $category"
            echo ""
            sort -u "$TEMP_DIR/$category"
            echo ""
        fi
    done
    
    # Output Other category as Miscellaneous if any
    if [ -s "$TEMP_DIR/Other" ]; then
        echo "### Miscellaneous"
        echo ""
        sort -u "$TEMP_DIR/Other"
        echo ""
    fi
    
} > "$OUTPUT_FILE"

# Report
ADDED=$(wc -l < "$TEMP_DIR/Added" | tr -d ' ')
FIXED=$(wc -l < "$TEMP_DIR/Fixed" | tr -d ' ')
CHANGED=$(wc -l < "$TEMP_DIR/Changed" | tr -d ' ')
REMOVED=$(wc -l < "$TEMP_DIR/Removed" | tr -d ' ')
DOCS=$(wc -l < "$TEMP_DIR/Docs" | tr -d ' ')
OTHER=$(wc -l < "$TEMP_DIR/Other" | tr -d ' ')
TOTAL=$((ADDED + FIXED + CHANGED + REMOVED + DOCS + OTHER))

echo -e "${GREEN}✓ Generated $OUTPUT_FILE${NC}"
echo -e "  ${ADDED} Added, ${FIXED} Fixed, ${CHANGED} Changed, ${REMOVED} Removed, ${DOCS} Docs, ${OTHER} Other"
echo -e "  Total: ${TOTAL} commits since ${SINCE_TAG}"