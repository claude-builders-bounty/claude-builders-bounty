#!/bin/bash
# Generate CHANGELOG from git history
# Usage: ./changelog.sh [--from TAG] [--to TAG] [--dry-run]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
FROM_TAG=""
TO_TAG="HEAD"
DRY_RUN=false
OUTPUT_FILE="CHANGELOG.md"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --from)
            FROM_TAG="$2"
            shift 2
            ;;
        --to)
            TO_TAG="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--from TAG] [--to TAG] [--dry-run]"
            exit 1
            ;;
    esac
done

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

# Find the last tag if FROM_TAG not specified
if [ -z "$FROM_TAG" ]; then
    FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -z "$FROM_TAG" ]; then
        echo -e "${YELLOW}No tags found. Generating changelog from all commits.${NC}"
        COMMIT_RANGE="$TO_TAG"
    else
        echo -e "${BLUE}Generating changelog from ${FROM_TAG} to ${TO_TAG}${NC}"
        COMMIT_RANGE="${FROM_TAG}..${TO_TAG}"
    fi
else
    echo -e "${BLUE}Generating changelog from ${FROM_TAG} to ${TO_TAG}${NC}"
    COMMIT_RANGE="${FROM_TAG}..${TO_TAG}"
fi

# Get current date
CURRENT_DATE=$(date +%Y-%m-%d)

# Initialize arrays for different categories
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

# Read commits and categorize
while IFS='|' read -r hash subject author date; do
    # Skip empty lines
    [ -z "$hash" ] && continue

    # Format: - Description (hash) by Author on Date
    entry="- ${subject#*: } (\`${hash}\`) by ${author} on ${date}"

    # Categorize by commit prefix
    case "$subject" in
        feat:*|feature:*|add:*)
            ADDED+=("$entry")
            ;;
        fix:*|bugfix:*|hotfix:*)
            FIXED+=("$entry")
            ;;
        change:*|update:*|refactor:*|perf:*)
            CHANGED+=("$entry")
            ;;
        remove:*|delete:*)
            REMOVED+=("$entry")
            ;;
        *)
            OTHER+=("$entry")
            ;;
    esac
done < <(git log "$COMMIT_RANGE" --pretty=format:"%h|%s|%an|%ad" --date=short 2>/dev/null)

# Generate changelog content
CHANGELOG_CONTENT="## [Unreleased] - ${CURRENT_DATE}

"

# Add sections if they have content
if [ ${#ADDED[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Added
"
    for item in "${ADDED[@]}"; do
        CHANGELOG_CONTENT+="${item}
"
    done
    CHANGELOG_CONTENT+="
"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Fixed
"
    for item in "${FIXED[@]}"; do
        CHANGELOG_CONTENT+="${item}
"
    done
    CHANGELOG_CONTENT+="
"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Changed
"
    for item in "${CHANGED[@]}"; do
        CHANGELOG_CONTENT+="${item}
"
    done
    CHANGELOG_CONTENT+="
"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Removed
"
    for item in "${REMOVED[@]}"; do
        CHANGELOG_CONTENT+="${item}
"
    done
    CHANGELOG_CONTENT+="
"
fi

if [ ${#OTHER[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Other
"
    for item in "${OTHER[@]}"; do
        CHANGELOG_CONTENT+="${item}
"
    done
    CHANGELOG_CONTENT+="
"
fi

# Add separator
CHANGELOG_CONTENT+="---

"

# Output or write to file
if [ "$DRY_RUN" = true ]; then
    echo -e "${GREEN}=== CHANGELOG PREVIEW ===${NC}"
    echo "$CHANGELOG_CONTENT"
else
    # Prepend to existing CHANGELOG.md or create new one
    if [ -f "$OUTPUT_FILE" ]; then
        # Backup existing file
        cp "$OUTPUT_FILE" "${OUTPUT_FILE}.bak"
        echo -e "${YELLOW}Backed up existing CHANGELOG.md to CHANGELOG.md.bak${NC}"

        # Prepend new content
        echo "$CHANGELOG_CONTENT" | cat - "$OUTPUT_FILE" > temp && mv temp "$OUTPUT_FILE"
        echo -e "${GREEN}✓ Updated ${OUTPUT_FILE}${NC}"
    else
        # Create new file with header
        cat > "$OUTPUT_FILE" << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

$CHANGELOG_CONTENT
EOF
        echo -e "${GREEN}✓ Created ${OUTPUT_FILE}${NC}"
    fi

    # Show summary
    total=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]}))
    echo -e "${BLUE}Summary:${NC}"
    echo "  Added: ${#ADDED[@]}"
    echo "  Fixed: ${#FIXED[@]}"
    echo "  Changed: ${#CHANGED[@]}"
    echo "  Removed: ${#REMOVED[@]}"
    echo "  Other: ${#OTHER[@]}"
    echo "  Total: $total commits"
fi
