#!/usr/bin/env bash

# changelog.sh - Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--output FILE] [--since TAG]
#   --output FILE   Output file (default: CHANGELOG.md)
#   --since TAG     Start from this tag (default: last tag, or all commits)

set -euo pipefail

# Default values
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --since)
            SINCE_TAG="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--output FILE] [--since TAG]"
            exit 1
            ;;
    esac
done

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Determine the starting point for commit history
if [[ -z "$SINCE_TAG" ]]; then
    # Find the last tag
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$LAST_TAG" ]]; then
        SINCE_TAG="$LAST_TAG"
        echo "Using last tag: $SINCE_TAG"
    else
        echo "No tags found. Including all commits."
    fi
fi

# Get commit log
if [[ -n "$SINCE_TAG" ]]; then
    COMMITS=$(git log "$SINCE_TAG"..HEAD --oneline --no-merges 2>/dev/null || git log --oneline --no-merges)
else
    COMMITS=$(git log --oneline --no-merges)
fi

# Check if we have any commits
if [[ -z "$COMMITS" ]]; then
    echo "No commits found."
    exit 0
fi

# Initialize category arrays
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Categorize commits
while IFS= read -r line; do
    # Extract commit message (skip hash)
    MESSAGE="${line#* }"
    
    # Determine category based on conventional commit prefix
    case "$MESSAGE" in
        feat:*|feature:*|add:*|added:*|implement:*|new:*)
            ADDED+=("${MESSAGE#*: }")
            ;;
        fix:*|bugfix:*|bug:*|hotfix:*|patch:*|correct:*)
            FIXED+=("${MESSAGE#*: }")
            ;;
        refactor:*|perf:*|performance:*|style:*|update:*|upgrade:*|improve:*)
            CHANGED+=("${MESSAGE#*: }")
            ;;
        revert:*|remove:*|removed:*|delete:*|deprecate:*)
            REMOVED+=("${MESSAGE#*: }")
            ;;
        chore:*|docs:*|test:*|ci:*|build:*)
            CHANGED+=("${MESSAGE#*: }")
            ;;
        *)
            # Default to Changed for unrecognized prefixes
            CHANGED+=("$MESSAGE")
            ;;
    esac
done <<< "$COMMITS"

# Generate the changelog content
generate_changelog() {
    local output=""
    
    # Header
    output+="# Changelog\n\n"
    
    # Determine version and date
    local version="Unreleased"
    local date=$(date +%Y-%m-%d)
    
    output+="## [$version] - $date\n\n"
    
    # Helper function to add a section
    add_section() {
        local title="$1"
        shift
        local items=("$@")
        
        if [[ ${#items[@]} -gt 0 ]]; then
            output+="### $title\n\n"
            for item in "${items[@]}"; do
                # Capitalize first letter
                item="$(tr '[:lower:]' '[:upper:]' <<< "${item:0:1}")${item:1}"
                output+="- $item\n"
            done
            output+="\n"
        fi
    }
    
    # Add sections in order
    add_section "Added" "${ADDED[@]}"
    add_section "Fixed" "${FIXED[@]}"
    add_section "Changed" "${CHANGED[@]}"
    add_section "Removed" "${REMOVED[@]}"
    
    echo -e "$output"
}

# Generate and write the changelog
CHANGELOG_CONTENT=$(generate_changelog)
echo -e "$CHANGELOG_CONTENT" > "$OUTPUT_FILE"

echo "Changelog generated: $OUTPUT_FILE"
echo "Summary:"
echo "  Added:   ${#ADDED[@]} commits"
echo "  Fixed:   ${#FIXED[@]} commits"
echo "  Changed: ${#CHANGED[@]} commits"
echo "  Removed: ${#REMOVED[@]} commits"