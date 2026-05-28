#!/usr/bin/env bash
# generate-changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [output_file] [since_tag]
#
# Arguments:
#   output_file  — Path to the output file (default: CHANGELOG.md)
#   since_tag    — Git tag to start from (default: last tag, or all commits)
#
# Requirements: git

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
SINCE_TAG="${2:-}"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Ensure we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository.${NC}" >&2
    exit 1
fi

# Determine the range
if [ -z "$SINCE_TAG" ]; then
    # Try to find the latest tag
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Build the git log range
if [ -n "$SINCE_TAG" ]; then
    RANGE="${SINCE_TAG}..HEAD"
    echo -e "${GREEN}Generating changelog since ${YELLOW}${SINCE_TAG}${NC}"
else
    RANGE="HEAD"
    echo -e "${YELLOW}No tags found. Generating changelog from all commits.${NC}"
fi

# Temporary files for each category
ADDED=$(mktemp)
FIXED=$(mktemp)
CHANGED=$(mktemp)
REMOVED=$(mktemp)
OTHER=$(mktemp)

cleanup() {
    rm -f "$ADDED" "$FIXED" "$CHANGED" "$REMOVED" "$OTHER"
}
trap cleanup EXIT

# Parse commits using conventional commit format
# Format: type(scope): description
while IFS= read -r line; do
    # Skip empty lines
    [ -z "$line" ] && continue
    
    # Extract hash and message
    hash=$(echo "$line" | cut -d' ' -f1)
    message=$(echo "$line" | cut -d' ' -f2-)
    
    # Categorize based on conventional commit type
    case "$message" in
        feat:*|feat\(*:*)
            echo "- ${message#feat: } ([${hash}](../../commit/${hash}))" >> "$ADDED"
            ;;
        fix:*|fix\(*:*)
            echo "- ${message#fix: } ([${hash}](../../commit/${hash}))" >> "$FIXED"
            ;;
        refactor:*|refactor\(*:*)
            echo "- ${message#refactor: } ([${hash}](../../commit/${hash}))" >> "$CHANGED"
            ;;
        perf:*|perf\(*:*)
            echo "- ${message#perf: } ([${hash}](../../commit/${hash}))" >> "$CHANGED"
            ;;
        docs:*|docs\(*:*)
            echo "- ${message#docs: } ([${hash}](../../commit/${hash}))" >> "$CHANGED"
            ;;
        style:*|style\(*:*)
            echo "- ${message#style: } ([${hash}](../../commit/${hash}))" >> "$CHANGED"
            ;;
        chore:*|chore\(*:*)
            echo "- ${message#chore: } ([${hash}](../../commit/${hash}))" >> "$CHANGED"
            ;;
        ci:*|ci\(*:*)
            echo "- ${message#ci: } ([${hash}](../../commit/${hash}))" >> "$CHANGED"
            ;;
        test:*|test\(*:*)
            echo "- ${message#test: } ([${hash}](../../commit/${hash}))" >> "$CHANGED"
            ;;
        remove:*|remove\(*:*|delete:*|delete\(*:*)
            echo "- ${message} ([${hash}](../../commit/${hash}))" >> "$REMOVED"
            ;;
        *)
            echo "- ${message} ([${hash}](../../commit/${hash}))" >> "$OTHER"
            ;;
    esac
done < <(git log "$RANGE" --pretty=format:"%h %s" --no-merges 2>/dev/null || git log --pretty=format:"%h %s" --no-merges)

# Get current date
DATE=$(date +%Y-%m-%d)

# Build the changelog
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/)."
    echo ""
    
    # Add unreleased section or tagged version
    if [ -n "$SINCE_TAG" ]; then
        echo "## [Unreleased] - ${DATE}"
    else
        echo "## [Unreleased] - ${DATE}"
    fi
    echo ""
    
    # Added section
    if [ -s "$ADDED" ]; then
        echo "### Added"
        echo ""
        cat "$ADDED"
        echo ""
    fi
    
    # Fixed section
    if [ -s "$FIXED" ]; then
        echo "### Fixed"
        echo ""
        cat "$FIXED"
        echo ""
    fi
    
    # Changed section
    if [ -s "$CHANGED" ]; then
        echo "### Changed"
        echo ""
        cat "$CHANGED"
        echo ""
    fi
    
    # Removed section
    if [ -s "$REMOVED" ]; then
        echo "### Removed"
        echo ""
        cat "$REMOVED"
        echo ""
    fi
    
    # Other changes (uncategorized)
    if [ -s "$OTHER" ]; then
        echo "### Other"
        echo ""
        cat "$OTHER"
        echo ""
    fi
} > "$OUTPUT_FILE"

# Count changes
TOTAL=$(git log "$RANGE" --oneline --no-merges 2>/dev/null | wc -l || git log --oneline --no-merges | wc -l)

echo -e "${GREEN}✓ Changelog generated: ${YELLOW}${OUTPUT_FILE}${NC}"
echo -e "${GREEN}  Total commits processed: ${YELLOW}${TOTAL}${NC}"

# Show summary
echo ""
echo "Summary:"
[ -s "$ADDED" ] && echo -e "  ${GREEN}Added: $(wc -l < "$ADDED" | tr -d ' ') items${NC}"
[ -s "$FIXED" ] && echo -e "  ${RED}Fixed: $(wc -l < "$FIXED" | tr -d ' ') items${NC}"
[ -s "$CHANGED" ] && echo -e "  ${YELLOW}Changed: $(wc -l < "$CHANGED" | tr -d ' ') items${NC}"
[ -s "$REMOVED" ] && echo -e "  ${RED}Removed: $(wc -l < "$REMOVED" | tr -d ' ') items${NC}"
[ -s "$OTHER" ] && echo -e "  ${YELLOW}Other: $(wc -l < "$OTHER" | tr -d ' ') items${NC}"
