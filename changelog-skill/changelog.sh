#!/usr/bin/env bash
set -euo pipefail

# Generate Changelog from git history
# Usage: ./changelog.sh [output_file]
# Default output: CHANGELOG.md

OUTPUT_FILE="${1:-CHANGELOG.md}"
TEMP_FILE=$(mktemp)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Cleanup on exit
trap 'rm -f "$TEMP_FILE"' EXIT

echo -e "${GREEN}Generating changelog...${NC}"

# Get the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
    echo -e "${YELLOW}Found tag: $LAST_TAG${NC}"
    RANGE="$LAST_TAG..HEAD"
else
    echo -e "${YELLOW}No tags found, using all commits${NC}"
    RANGE=""
fi

# Get commits (excluding merge commits)
if [ -n "$RANGE" ]; then
    COMMITS=$(git log "$RANGE" --oneline --no-merges --format="%H|%s|%an|%ad" --date=short 2>/dev/null || echo "")
else
    COMMITS=$(git log --oneline --no-merges --format="%H|%s|%an|%ad" --date=short 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
    echo -e "${RED}No commits found${NC}"
    echo "# Changelog" > "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "No changes found." >> "$OUTPUT_FILE"
    exit 0
fi

# Initialize sections
BREAKING=""
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# Parse each commit
while IFS='|' read -r hash message author date; do
    # Skip empty lines
    [ -z "$hash" ] && continue
    
    # Extract PR number if present
    PR_NUM=""
    if [[ "$message" =~ \(#([0-9]+)\) ]]; then
        PR_NUM="${BASH_REMATCH[1]}"
    fi
    
    # Extract conventional commit type
    TYPE=""
    SCOPE=""
    DESC="$message"
    IS_BREAKING=false
    
    # Parse conventional commit format using string manipulation
    # Format: type(scope): description or type: description
    if [[ "$message" == *": "* ]]; then
        # Split on first ": "
        BEFORE="${message%%": "*}"
        AFTER="${message#*": "}"
        
        # Check if BEFORE contains a scope in parentheses
        if [[ "$BEFORE" == *"("*")"* ]]; then
            TYPE="${BEFORE%%"("*}"
            SCOPE="${BEFORE#*"("}"
            SCOPE="${SCOPE%")"}"
        else
            TYPE="$BEFORE"
        fi
        DESC="$AFTER"
        
        # Check for breaking change indicator (! suffix on type)
        if [[ "$TYPE" == *"!"* ]]; then
            IS_BREAKING=true
            # Remove ! from type
            TYPE="${TYPE%!}"
        fi
    fi
    
    # Format the entry
    ENTRY=""
    if [ -n "$SCOPE" ]; then
        ENTRY="- **${SCOPE}**: ${DESC}"
    else
        ENTRY="- ${DESC}"
    fi
    
    if [ -n "$PR_NUM" ]; then
        ENTRY="${ENTRY} (#${PR_NUM})"
    fi
    
    # Categorize by type
    case "$TYPE" in
        feat)
            ADDED="${ADDED}${ENTRY}\n"
            ;;
        fix)
            FIXED="${FIXED}${ENTRY}\n"
            ;;
        refactor|perf)
            CHANGED="${CHANGED}${ENTRY}\n"
            ;;
        docs)
            CHANGED="${CHANGED}${ENTRY}\n"
            ;;
        chore|build|ci)
            CHANGED="${CHANGED}${ENTRY}\n"
            ;;
        revert)
            REMOVED="${REMOVED}${ENTRY}\n"
            ;;
        *)
            # Default to Changed for non-conventional commits
            CHANGED="${CHANGED}${ENTRY}\n"
            ;;
    esac
    
    # Add to breaking changes if marked as breaking
    if [ "$IS_BREAKING" = true ]; then
        BREAKING="${BREAKING}${ENTRY}\n"
    fi
    
    # Also check for BREAKING CHANGE in commit message
    if [[ "$message" =~ BREAKING\ CHANGE ]]; then
        # Only add if not already in breaking
        if [[ "$BREAKING" != *"$ENTRY"* ]]; then
            BREAKING="${BREAKING}${ENTRY}\n"
        fi
    fi
done <<< "$COMMITS"

# Generate the changelog
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    
    if [ -n "$LAST_TAG" ]; then
        echo "## [Unreleased] (since ${LAST_TAG})"
    else
        echo "## [Unreleased]"
    fi
    echo ""
    
    # Breaking changes first
    if [ -n "$BREAKING" ]; then
        echo "### ⚠️ Breaking Changes"
        echo ""
        echo -e "$BREAKING"
    fi
    
    # Added
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo ""
        echo -e "$ADDED"
    fi
    
    # Fixed
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo ""
        echo -e "$FIXED"
    fi
    
    # Changed
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo ""
        echo -e "$CHANGED"
    fi
    
    # Removed
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo ""
        echo -e "$REMOVED"
    fi
    
} > "$TEMP_FILE"

# Check if we have any changes
if [ -z "$BREAKING" ] && [ -z "$ADDED" ] && [ -z "$FIXED" ] && [ -z "$CHANGED" ] && [ -z "$REMOVED" ]; then
    {
        echo "# Changelog"
        echo ""
        echo "All notable changes to this project will be documented in this file."
        echo ""
        echo "## [Unreleased]"
        echo ""
        echo "No changes found."
    } > "$TEMP_FILE"
fi

# Move to output file
mv "$TEMP_FILE" "$OUTPUT_FILE"

TOTAL=$(echo "$COMMITS" | wc -l | tr -d ' ')
echo -e "${GREEN}✓ Changelog generated: ${OUTPUT_FILE}${NC}"
echo -e "${GREEN}  Total commits: ${TOTAL}${NC}"
