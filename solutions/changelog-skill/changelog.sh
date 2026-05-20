#!/bin/bash
#
# CHANGELOG Generator
# Automatically generates a structured CHANGELOG.md from git history
#
# Usage:
#   ./changelog.sh              # Generate since last tag
#   ./changelog.sh v1.0.0       # Generate up to specific tag
#   ./changelog.sh v1.0.0..v2.0.0  # Generate for tag range
#   ./changelog.sh --last 50    # Generate for last N commits
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
RANGE=""
LAST_N=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --last)
            LAST_N="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options] [tag|range]"
            echo ""
            echo "Options:"
            echo "  --last N     Generate changelog for last N commits"
            echo "  -h, --help   Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Since last tag"
            echo "  $0 v1.0.0             # Up to v1.0.0"
            echo "  $0 v1.0.0..v2.0.0     # Between tags"
            echo "  $0 --last 50          # Last 50 commits"
            exit 0
            ;;
        *)
            RANGE="$1"
            shift
            ;;
    esac
done

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Determine commit range
if [ -n "$LAST_N" ]; then
    COMMIT_RANGE="--last $LAST_N"
    COMMITS=$(git log --pretty=format:"%h|%s|%an|%ad" --date=short -n "$LAST_N" 2>/dev/null || true)
elif [ -n "$RANGE" ]; then
    if [[ "$RANGE" == *".."* ]]; then
        # Tag range provided
        COMMIT_RANGE="$RANGE"
        COMMITS=$(git log "$RANGE" --pretty=format:"%h|%s|%an|%ad" --date=short 2>/dev/null || true)
    else
        # Single tag provided
        COMMIT_RANGE="up to $RANGE"
        COMMITS=$(git log --pretty=format:"%h|%s|%an|%ad" --date=short "$RANGE" 2>/dev/null || true)
    fi
else
    # Get last tag
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -n "$LAST_TAG" ]; then
        COMMIT_RANGE="since $LAST_TAG"
        COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%h|%s|%an|%ad" --date=short 2>/dev/null || true)
    else
        COMMIT_RANGE="last 50 commits (no tags found)"
        COMMITS=$(git log --pretty=format:"%h|%s|%an|%ad" --date=short -50 2>/dev/null || true)
    fi
fi

if [ -z "$COMMITS" ]; then
    echo -e "${YELLOW}No commits found in the specified range${NC}"
    exit 0
fi

echo -e "${GREEN}Generating CHANGELOG.md ${COMMIT_RANGE}...${NC}"

# Arrays for categories
declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED
declare -a DEPRECATED
declare -a SECURITY

# Categorize commits
while IFS='|' read -r hash message author date; do
    # Skip merge commits (unless they have meaningful content)
    if [[ "$message" =~ ^Merge\ (pull\ request|branch) ]] && [[ ! "$message" =~ \#[0-9]+ ]]; then
        continue
    fi

    # Skip changelog skip markers
    if [[ "$message" =~ \[skip\ changelog\] ]] || [[ "$message" =~ \[ci\ skip\] ]]; then
        continue
    fi

    # Extract PR/issue reference
    REF=""
    if [[ "$message" =~ \#([0-9]+) ]]; then
        REF=" (#${BASH_REMATCH[1]})"
    fi

    # Clean message (remove conventional commit prefixes and references)
    CLEAN_MSG=$(echo "$message" | sed -E 's/^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)(\(.+\))?:\s*//' | sed 's/#[0-9]*$//' | sed 's/ ([^)]*)$//' | sed 's/^\s*//')
    CLEAN_MSG=$(echo "$CLEAN_MSG" | sed 's/(#[0-9]*)$//')

    # Capitalize first letter
    CLEAN_MSG=$(echo "$CLEAN_MSG" | sed 's/^\(.\)/\U\1/')

    # Categorize based on conventional commit prefixes or keywords
    MSG_LOWER=$(echo "$message" | tr '[:upper:]' '[:lower:]')

    if [[ "$message" =~ ^feat:|^feature: ]] || [[ "$MSG_LOWER" =~ ^add|^new\ (feature|support|option) ]] || [[ "$MSG_LOWER" =~ ^implement ]]; then
        ADDED+=("- $CLEAN_MSG$REF")
    elif [[ "$message" =~ ^fix:|^bugfix: ]] || [[ "$MSG_LOWER" =~ ^fix|^resolve|^correct|^repair ]] || [[ "$MSG_LOWER" =~ ^bugfix ]]; then
        FIXED+=("- $CLEAN_MSG$REF")
    elif [[ "$message" =~ ^refactor:|^change:|^update: ]] || [[ "$MSG_LOWER" =~ ^update|^change|^modify|^improve|^refactor|^enhance ]]; then
        CHANGED+=("- $CLEAN_MSG$REF")
    elif [[ "$message" =~ ^remove:|^delete: ]] || [[ "$MSG_LOWER" =~ ^remove|^delete|^drop ]]; then
        REMOVED+=("- $CLEAN_MSG$REF")
    elif [[ "$message" =~ ^deprecate: ]] || [[ "$MSG_LOWER" =~ ^deprecate ]]; then
        DEPRECATED+=("- $CLEAN_MSG$REF")
    elif [[ "$message" =~ ^security:|^sec: ]] || [[ "$MSG_LOWER" =~ ^security|^cve- ]]; then
        SECURITY+=("- $CLEAN_MSG$REF")
    else
        # Default category based on keywords
        if [[ "$MSG_LOWER" =~ add|new|implement|introduce ]]; then
            ADDED+=("- $CLEAN_MSG$REF")
        elif [[ "$MSG_LOWER" =~ fix|resolve|correct|repair ]]; then
            FIXED+=("- $CLEAN_MSG$REF")
        elif [[ "$MSG_LOWER" =~ update|change|modify|improve|refactor|enhance|optimize ]]; then
            CHANGED+=("- $CLEAN_MSG$REF")
        elif [[ "$MSG_LOWER" =~ remove|delete|drop ]]; then
            REMOVED+=("- $CLEAN_MSG$REF")
        else
            CHANGED+=("- $CLEAN_MSG$REF")
        fi
    fi
done <<< "$COMMITS"

# Generate CHANGELOG content
CURRENT_DATE=$(date +%Y-%m-%d)
VERSION="Unreleased"

# Get version from tag if available
if [ -n "$LAST_TAG" ]; then
    VERSION="${LAST_TAG#v}"
fi

CHANGELOG_CONTENT="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [$VERSION] - $CURRENT_DATE

"

# Add categories
if [ ${#ADDED[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Added
"
    for item in "${ADDED[@]}"; do
        CHANGELOG_CONTENT+="$item
"
    done
    CHANGELOG_CONTENT+="
"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Changed
"
    for item in "${CHANGED[@]}"; do
        CHANGELOG_CONTENT+="$item
"
    done
    CHANGELOG_CONTENT+="
"
fi

if [ ${#DEPRECATED[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Deprecated
"
    for item in "${DEPRECATED[@]}"; do
        CHANGELOG_CONTENT+="$item
"
    done
    CHANGELOG_CONTENT+="
"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Removed
"
    for item in "${REMOVED[@]}"; do
        CHANGELOG_CONTENT+="$item
"
    done
    CHANGELOG_CONTENT+="
"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Fixed
"
    for item in "${FIXED[@]}"; do
        CHANGELOG_CONTENT+="$item
"
    done
    CHANGELOG_CONTENT+="
"
fi

if [ ${#SECURITY[@]} -gt 0 ]; then
    CHANGELOG_CONTENT+="### Security
"
    for item in "${SECURITY[@]}"; do
        CHANGELOG_CONTENT+="$item
"
    done
    CHANGELOG_CONTENT+="
"
fi

# Handle existing CHANGELOG.md
if [ -f "CHANGELOG.md" ]; then
    # Read existing content, skipping header
    EXISTING=$(tail -n +8 CHANGELOG.md 2>/dev/null || echo "")
    echo "$CHANGELOG_CONTENT" > CHANGELOG.md
    echo "$EXISTING" >> CHANGELOG.md
else
    echo "$CHANGELOG_CONTENT" > CHANGELOG.md
fi

# Summary
TOTAL_COMMITS=$(echo "$COMMITS" | wc -l | tr -d ' ')
echo -e "${GREEN}✓ Generated CHANGELOG.md${NC}"
echo "  Commits analyzed: $TOTAL_COMMITS"
echo "  Added: ${#ADDED[@]}"
echo "  Fixed: ${#FIXED[@]}"
echo "  Changed: ${#CHANGED[@]}"
echo "  Removed: ${#REMOVED[@]}"
echo "  Deprecated: ${#DEPRECATED[@]}"
echo "  Security: ${#SECURITY[@]}"