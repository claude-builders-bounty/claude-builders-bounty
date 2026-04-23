#!/usr/bin/env bash
#
# Changelog Generator
# Generates a structured CHANGELOG.md from git history since last tag
#
# Usage: bash changelog.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the latest tag, or use initial commit if no tags exist
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

if [[ "$LAST_TAG" == "$(git rev-list --max-parents=0 HEAD)" ]]; then
    echo -e "${YELLOW}No tags found. Generating changelog from all commits.${NC}"
    TAG_RANGE="$LAST_TAG..HEAD"
else
    echo -e "${GREEN}Latest tag: $LAST_TAG${NC}"
    TAG_RANGE="$LAST_TAG..HEAD"
fi

# Get commits since last tag
COMMITS=$(git log "$TAG_RANGE" --pretty=format:"%s" --no-merges)

if [[ -z "$COMMITS" ]]; then
    echo -e "${YELLOW}No new commits since $LAST_TAG${NC}"
    exit 0
fi

# Initialize categories
declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED
declare -a OTHER

# Categorize commits based on conventional commit prefixes
while IFS= read -r commit; do
    case "$commit" in
        feat:*|add:*)
            ADDED+=("${commit#*: }")
            ;;
        fix:*|bug:*)
            FIXED+=("${commit#*: }")
            ;;
        refactor:*|update:*|change:*|chore:*)
            CHANGED+=("${commit#*: }")
            ;;
        remove:*|delete:*)
            REMOVED+=("${commit#*: }")
            ;;
        *)
            # Check if commit starts with a verb
            if [[ "$commit" =~ ^(Add|Fix|Change|Update|Remove|Delete|Refactor)[[:space:]] ]]; then
                first_word=$(echo "$commit" | awk '{print $1}')
                rest=$(echo "$commit" | cut -d' ' -f2-)
                case "$first_word" in
                    Add|Added)
                        ADDED+=("$rest")
                        ;;
                    Fix|Fixed)
                        FIXED+=("$rest")
                        ;;
                    Change|Changed|Update|Updated|Refactor|Refactored)
                        CHANGED+=("$rest")
                        ;;
                    Remove|Removed|Delete|Deleted)
                        REMOVED+=("$rest")
                        ;;
                    *)
                        OTHER+=("$commit")
                        ;;
                esac
            else
                OTHER+=("$commit")
            fi
            ;;
    esac
done <<< "$COMMITS"

# Generate CHANGELOG.md
CHANGELOG_FILE="CHANGELOG.md"
TODAY=$(date +%Y-%m-%d)

# Read existing changelog if it exists
EXISTING_CHANGELOG=""
if [[ -f "$CHANGELOG_FILE" ]]; then
    EXISTING_CHANGELOG=$(cat "$CHANGELOG_FILE")
fi

# Create new changelog content
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)."
    echo ""

    # New version section
    echo "## [Unreleased] - $TODAY"
    echo ""

    # Added
    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        echo ""
        for item in "${ADDED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    # Fixed
    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        echo ""
        for item in "${FIXED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    # Changed
    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        echo ""
        for item in "${CHANGED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    # Removed
    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        echo ""
        for item in "${REMOVED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    # Other (if any)
    if [[ ${#OTHER[@]} -gt 0 ]]; then
        echo "### Other"
        echo ""
        for item in "${OTHER[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    # Append existing changelog (skip header if it exists)
    if [[ -n "$EXISTING_CHANGELOG" ]]; then
        echo "$EXISTING_CHANGELOG" | sed '1,/^## /d'
    fi
} > "$CHANGELOG_FILE"

echo -e "${GREEN}✓ CHANGELOG.md generated successfully!${NC}"
echo ""
echo "Summary:"
echo "  Added: ${#ADDED[@]}"
echo "  Fixed: ${#FIXED[@]}"
echo "  Changed: ${#CHANGED[@]}"
echo "  Removed: ${#REMOVED[@]}"
[[ ${#OTHER[@]} -gt 0 ]] && echo "  Other: ${#OTHER[@]}"
echo ""
echo -e "${YELLOW}Review CHANGELOG.md and update version number before committing.${NC}"
