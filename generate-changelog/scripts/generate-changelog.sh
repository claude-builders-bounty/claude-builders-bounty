#!/bin/bash
#
# Generate CHANGELOG.md from git history
# Supports conventional commits: feat, fix, docs, style, refactor, perf, test, chore, revert
#

set -e

# Default values
OUTPUT_FILE="CHANGELOG.md"
FROM_TAG=""
TO_TAG=""
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --from-tag)
            FROM_TAG="$2"
            shift 2
            ;;
        --to-tag)
            TO_TAG="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get git repo root
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [[ -z "$GIT_ROOT" ]]; then
    echo "Error: Not a git repository"
    exit 1
fi

cd "$GIT_ROOT"

# Get tags and determine range
if [[ -z "$FROM_TAG" ]]; then
    # Get the latest tag (or first commit if no tags)
    FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -z "$TO_TAG" ]]; then
    TO_TAG="HEAD"
fi

# Build git log range
if [[ -n "$FROM_TAG" ]]; then
    GIT_RANGE="$FROM_TAG..$TO_TAG"
else
    # No tags, get all commits
    GIT_RANGE="$TO_TAG"
fi

# Get current date
CURRENT_DATE=$(date +"%Y-%m-%d")

# Initialize arrays for each category
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

# Function to categorize commit
categorize_commit() {
    local msg="$1"
    local type=$(echo "$msg" | grep -oE "^(feat|fix|perf|refactor|docs|style|test|chore|revert)" | head -1)
    local desc=$(echo "$msg" | sed -E 's/^[a-z]+\(\w+\)!?:\s*//' | sed -E 's/^[^:]+:\s*//')
    
    case "$type" in
        feat)
            ADDED+=("$desc")
            ;;
        fix)
            FIXED+=("$desc")
            ;;
        refactor|perf|docs|style)
            CHANGED+=("$desc")
            ;;
        revert)
            REMOVED+=("$desc")
            ;;
        test|chore|ci|build)
            OTHER+=("$desc")
            ;;
        *)
            # If no conventional prefix, add to Other
            if [[ -n "$msg" ]]; then
                OTHER+=("$msg")
            fi
            ;;
    esac
}

# Parse git log
echo "Fetching commits from $GIT_RANGE..."
while IFS= read -r line; do
    if [[ -n "$line" ]]; then
        categorize_commit "$line"
    fi
done < <(git log "$GIT_RANGE" --pretty=format:"%s" 2>/dev/null)

# Build changelog content
build_changelog() {
    local output=""
    
    output+="# Changelog\n"
    output+="\n"
    output+="All notable changes to this project will be documented in this file.\n"
    output+="\n"
    
    # Get version tag for header
    if [[ -n "$FROM_TAG" ]]; then
        local version="$FROM_TAG"
    else
        local version="Unreleased"
    fi
    output+="## [$version] - $CURRENT_DATE\n"
    output+="\n"
    
    # Added section
    if [[ ${#ADDED[@]} -gt 0 ]]; then
        output+="### Added\n"
        for item in "${ADDED[@]}"; do
            output+="- $item\n"
        done
        output+="\n"
    fi
    
    # Fixed section
    if [[ ${#FIXED[@]} -gt 0 ]]; then
        output+="### Fixed\n"
        for item in "${FIXED[@]}"; do
            output+="- $item\n"
        done
        output+="\n"
    fi
    
    # Changed section
    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        output+="### Changed\n"
        for item in "${CHANGED[@]}"; do
            output+="- $item\n"
        done
        output+="\n"
    fi
    
    # Removed section
    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        output+="### Removed\n"
        for item in "${REMOVED[@]}"; do
            output+="- $item\n"
        done
        output+="\n"
    fi
    
    # Other section
    if [[ ${#OTHER[@]} -gt 0 ]]; then
        output+="### Other\n"
        for item in "${OTHER[@]}"; do
            output+="- $item\n"
        done
        output+="\n"
    fi
    
    echo -e "$output"
}

# Generate changelog
CHANGELOG=$(build_changelog)

if [[ "$DRY_RUN" == true ]]; then
    echo "=== Generated CHANGELOG (dry run) ==="
    echo "$CHANGELOG"
else
    echo "$CHANGELOG" > "$OUTPUT_FILE"
    echo "✓ CHANGELOG generated: $OUTPUT_FILE"
    echo ""
    echo "Summary:"
    [[ ${#ADDED[@]} -gt 0 ]] && echo "  Added:   ${#ADDED[@]} items"
    [[ ${#FIXED[@]} -gt 0 ]] && echo "  Fixed:   ${#FIXED[@]} items"
    [[ ${#CHANGED[@]} -gt 0 ]] && echo "  Changed: ${#CHANGED[@]} items"
    [[ ${#REMOVED[@]} -gt 0 ]] && echo "  Removed: ${#REMOVED[@]} items"
    [[ ${#OTHER[@]} -gt 0 ]] && echo "  Other:   ${#OTHER[@]} items"
fi
