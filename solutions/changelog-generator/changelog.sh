#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [output_file] [--full]
#   output_file:  file to write (default: CHANGELOG.md)
#   --full:       include all commits since the beginning (ignore tags)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="${1:-CHANGELOG.md}"
USE_FULL="${2:-}"

# ── Colors for output ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Check prerequisites ──
if ! command -v git &>/dev/null; then
    echo -e "${RED}Error: git is not installed${NC}" >&2
    exit 1
fi

# ── Determine the commit range ──
if [ "$USE_FULL" = "--full" ]; then
    RANGE="HEAD"
    echo -e "${YELLOW}Generating full changelog (all commits)...${NC}"
else
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -z "$LAST_TAG" ]; then
        echo -e "${YELLOW}No tags found. Generating changelog from all commits.${NC}"
        RANGE="HEAD"
    else
        RANGE="${LAST_TAG}..HEAD"
        echo -e "${GREEN}Last tag: ${LAST_TAG}${NC}"
        echo "Commit range: ${RANGE}"
    fi
fi

# ── Get the current version ──
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
NEXT_TAG="${CURRENT_TAG}"

# Try to determine next version from commits
if git rev-parse "HEAD" &>/dev/null; then
    # Simple heuristic: bump patch version
    if [[ $CURRENT_TAG =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
        MAJOR="${BASH_REMATCH[1]}"
        MINOR="${BASH_REMATCH[2]}"
        PATCH="${BASH_REMATCH[3]}"
        NEXT_TAG="${MAJOR}.${MINOR}.$((PATCH + 1))"
    fi
fi

# ── Fetch commits and categorize ──
echo -e "${BLUE}Fetching commits...${NC}"

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
UNCATEGORIZED=()

while IFS= read -r line; do
    HASH=$(echo "$line" | cut -f1)
    SUBJECT=$(echo "$line" | cut -f2-)
    
    # Normalize for classification
    LOWERCASE=$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')
    
    # Categorize based on conventional commit prefix
    if echo "$LOWERCASE" | grep -qE '^(feat|feature|add|implement|create|introduce)\b'; then
        ADDED+=("$HASH||$SUBJECT")
    elif echo "$LOWERCASE" | grep -qE '^(fix|bugfix|bug|hotfix|patch|correct|resolve)\b'; then
        FIXED+=("$HASH||$SUBJECT")
    elif echo "$LOWERCASE" | grep -qE '^(change|update|modify|refactor|improve|optimize|perf|migrate|bump)\b'; then
        CHANGED+=("$HASH||$SUBJECT")
    elif echo "$LOWERCASE" | grep -qE '^(remove|delete|drop|deprecate|cleanup|purge)\b'; then
        REMOVED+=("$HASH||$SUBJECT")
    elif echo "$LOWERCASE" | grep -qE '^(docs?|style|test|chore|ci|build|config)\b'; then
        # These are maintenance — skip or put in Changed
        CHANGED+=("$HASH||$SUBJECT")
    else
        UNCATEGORIZED+=("$HASH||$SUBJECT")
    fi
done < <(git log "${RANGE}" --format="%h%x09%s" --no-merges 2>/dev/null || true)

# ── Generate the CHANGELOG.md ──
{
    echo "# Changelog"
    echo ""
    echo "## [${NEXT_TAG}] - $(date +%Y-%m-%d)"
    echo ""

    # Added
    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        for entry in "${ADDED[@]}"; do
            HASH="${entry%%||*}"
            MSG="${entry#*||}"
            echo "- ${MSG} (${HASH})"
        done
        echo ""
    fi

    # Fixed
    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        for entry in "${FIXED[@]}"; do
            HASH="${entry%%||*}"
            MSG="${entry#*||}"
            echo "- ${MSG} (${HASH})"
        done
        echo ""
    fi

    # Changed
    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        for entry in "${CHANGED[@]}"; do
            HASH="${entry%%||*}"
            MSG="${entry#*||}"
            echo "- ${MSG} (${HASH})"
        done
        echo ""
    fi

    # Removed
    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        for entry in "${REMOVED[@]}"; do
            HASH="${entry%%||*}"
            MSG="${entry#*||}"
            echo "- ${MSG} (${HASH})"
        done
        echo ""
    fi

    # Uncategorized (fallback)
    if [ ${#UNCATEGORIZED[@]} -gt 0 ] && [ "$USE_FULL" = "--full" ]; then
        echo "### Other"
        for entry in "${UNCATEGORIZED[@]}"; do
            HASH="${entry%%||*}"
            MSG="${entry#*||}"
            echo "- ${MSG} (${HASH})"
        done
        echo ""
    fi
} > "$OUTPUT_FILE"

echo ""
echo -e "${GREEN}✅ Changelog generated: ${OUTPUT_FILE}${NC}"

# ── Summary ──
echo ""
echo "  📊 Summary:"
echo "     Added:   ${#ADDED[@]}"
echo "     Fixed:   ${#FIXED[@]}"
echo "     Changed: ${#CHANGED[@]}"
echo "     Removed: ${#REMOVED[@]}"
if [ ${#UNCATEGORIZED[@]} -gt 0 ]; then
    echo "     Other:   ${#UNCATEGORIZED[@]}"
fi
echo ""
echo -e "${BLUE}Total commits: $(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#UNCATEGORIZED[@]} ))${NC}"
