#!/usr/bin/env bash
# changelog.sh - Generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [--since TAG] [--output FILE] [--dry-run]

set -euo pipefail

# Default values
SINCE_TAG=""
OUTPUT_FILE="CHANGELOG.md"
DRY_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Generate a structured CHANGELOG.md from git history.

Options:
    --since TAG       Generate changelog since this tag (default: last tag)
    --output FILE     Output file (default: CHANGELOG.md)
    --dry-run         Print to stdout instead of writing file
    -h, --help        Show this help message

Examples:
    $0                          # Generate from last tag to HEAD
    $0 --since v1.0.0           # Generate since specific tag
    $0 --output CHANGES.md      # Custom output file
    $0 --dry-run                # Preview without writing
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --since)
            SINCE_TAG="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}" >&2
            usage
            exit 1
            ;;
    esac
done

# Check if we're in a git repository
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}" >&2
    exit 1
fi

# Get the latest tag if not specified
if [[ -z "$SINCE_TAG" ]]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Determine the commit range
if [[ -n "$SINCE_TAG" ]]; then
    # Verify tag exists
    if ! git rev-parse "$SINCE_TAG" >/dev/null 2>&1; then
        echo -e "${RED}Error: Tag '$SINCE_TAG' not found${NC}" >&2
        exit 1
    fi
    COMMIT_RANGE="${SINCE_TAG}..HEAD"
    RANGE_DESC="since $SINCE_TAG"
else
    COMMIT_RANGE="HEAD"
    RANGE_DESC="all commits"
fi

# Get commits with conventional commit format parsing
# Format: type(scope): description
# We'll categorize based on type prefix

get_commits() {
    git log --pretty=format:"%H|%s|%b%n" --no-merges "$COMMIT_RANGE" 2>/dev/null
}

# Categorize commits
declare -A ADDED=() FIXED=() CHANGED=() REMOVED=() OTHER=()

while IFS='|' read -r hash subject body; do
    [[ -z "$hash" ]] && continue
    
    # Extract type from conventional commit format
    # Matches: feat, fix, chore, docs, style, refactor, perf, test, build, ci, revert, etc.
    type=""
    scope=""
    description="$subject"
    
    regex1='^([a-zA-Z]+)(\([^)]+\))?!?: (.+)$'
    regex2='^([A-Z]+): (.+)$'
    if [[ "$subject" =~ $regex1 ]]; then
        type="${BASH_REMATCH[1],,}"
        scope="${BASH_REMATCH[2]}"
        description="${BASH_REMATCH[3]}"
    elif [[ "$subject" =~ $regex2 ]]; then
        # Handle uppercase types like "FEAT: description"
        type="${BASH_REMATCH[1],,}"
        description="${BASH_REMATCH[2]}"
    fi
    
    # Categorize based on type
    case "$type" in
        feat|feature|add|added)
            ADDED["$hash"]="$description"
            ;;
        fix|bug|bugfix|hotfix)
            FIXED["$hash"]="$description"
            ;;
        refactor|refact|change|changed|update|updated|modify|modified)
            CHANGED["$hash"]="$description"
            ;;
        remove|removed|delete|deleted|rm)
            REMOVED["$hash"]="$description"
            ;;
        *)
            # Check description for keywords if no conventional type
            lower_desc="${description,,}"
            if [[ "$lower_desc" =~ ^(add|feat|feature|introduce|implement) ]]; then
                ADDED["$hash"]="$description"
            elif [[ "$lower_desc" =~ ^(fix|resolve|repair|patch|hotfix) ]]; then
                FIXED["$hash"]="$description"
            elif [[ "$lower_desc" =~ ^(change|update|modify|refactor|improve|enhance) ]]; then
                CHANGED["$hash"]="$description"
            elif [[ "$lower_desc" =~ ^(remove|delete|drop|eliminate) ]]; then
                REMOVED["$hash"]="$description"
            else
                OTHER["$hash"]="$description"
            fi
            ;;
    esac
done < <(get_commits)

# Generate changelog content
generate_changelog() {
    local today
    today=$(date +%Y-%m-%d)
    
    cat <<EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [$today] - $RANGE_DESC

EOF

    # Added section
    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        for hash in "${!ADDED[@]}"; do
            echo "- ${ADDED[$hash]}"
        done
        echo ""
    fi

    # Fixed section
    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        for hash in "${!FIXED[@]}"; do
            echo "- ${FIXED[$hash]}"
        done
        echo ""
    fi

    # Changed section
    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        for hash in "${!CHANGED[@]}"; do
            echo "- ${CHANGED[$hash]}"
        done
        echo ""
    fi

    # Removed section
    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        for hash in "${!REMOVED[@]}"; do
            echo "- ${REMOVED[$hash]}"
        done
        echo ""
    fi

    # Other section (if any)
    if [[ ${#OTHER[@]} -gt 0 ]]; then
        echo "### Other"
        for hash in "${!OTHER[@]}"; do
            echo "- ${OTHER[$hash]}"
        done
        echo ""
    fi

    # If no commits at all
    if [[ ${#ADDED[@]} -eq 0 && ${#FIXED[@]} -eq 0 && ${#CHANGED[@]} -eq 0 && ${#REMOVED[@]} -eq 0 && ${#OTHER[@]} -eq 0 ]]; then
        echo "_No changes recorded._"
        echo ""
    fi
}

# Output
if [[ "$DRY_RUN" == true ]]; then
    generate_changelog
else
    generate_changelog > "$OUTPUT_FILE"
    echo -e "${GREEN}✓${NC} Changelog generated: $OUTPUT_FILE"
fi