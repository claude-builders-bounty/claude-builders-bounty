#!/bin/bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since-tag <tag>] [--output <file>]

set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE_TAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --since-tag)
            SINCE_TAG="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--since-tag <tag>] [--output <file>]"
            exit 1
            ;;
    esac
done

# Verify we're in a git repo
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

# Determine range
if [[ -n "$SINCE_TAG" ]]; then
    if ! git rev-parse "$SINCE_TAG" > /dev/null 2>&1; then
        echo "Error: Tag '$SINCE_TAG' not found"
        exit 1
    fi
    RANGE="$SINCE_TAG..HEAD"
else
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$LAST_TAG" ]]; then
        RANGE="$LAST_TAG..HEAD"
    else
        RANGE="--all"
    fi
fi

# Fetch commits — use null byte as separator (printf %s\0 for safety)
# git log --format with %s and %h separated by a sentinel
mapfile -t LINES < <(git log "$RANGE" --pretty=format:"%s%GFG%gh%GFG" 2>/dev/null || true)

if [[ ${#LINES[@]} -eq 0 ]]; then
    echo "No commits found in range"
    exit 0
fi

# Sentinel to split msg from hash
SENTINEL="<<<GITSPLIT>>>"

# Re-fetch with a better delimiter approach using process substitution
COMMITS=$(git log "$RANGE" --format="COMMITBEGIN%sCOMMITEND%h" 2>/dev/null || echo "")

# Initialize categorized associative array
declare -A ITEMS
ITEMS[Added]=""
ITEMS[Fixed]=""
ITEMS[Changed]=""
ITEMS[Removed]=""
ITEMS[Security]=""
ITEMS[Other]=""

# Parse commits using sed
while IFS= read -r line; do
    # Split on COMMITBEGIN / COMMITEND
    msg=$(echo "$line" | sed 's/COMMITBEGIN\(.*\)COMMITEND.*/\1/')
    hash=$(echo "$line" | sed 's/.*COMMITEND//')
    
    [[ -z "$msg" ]] && continue

    category="Other"
    lc_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

    case "$lc_msg" in
        feat:*|feature:*|add:*|new:*)
            category="Added"
            ;;
        fix:*|bugfix:*|patch:*|hotfix:*)
            category="Fixed"
            ;;
        refactor:*|perf:*|optimize:*|improve:*|chore:*|style:*|format:*)
            category="Changed"
            ;;
        remove:*|delete:*|deprecate:*|drop:*)
            category="Removed"
            ;;
        security:*|sec:*)
            category="Security"
            ;;
        docs:*|doc:*|test:*|tests:*|ci:*|build:*)
            category="Changed"
            ;;
    esac

    line_formatted="- $msg (#$hash)"
    if [[ -n "${ITEMS[$category]}" ]]; then
        ITEMS[$category]="${line_formatted}"$'\n'"${ITEMS[$category]}"
    else
        ITEMS[$category]="$line_formatted"
    fi
done < <(echo "$COMMITS")

# Determine version header
CURRENT_DATE=$(date "+%Y-%m-%d")
if [[ -n "${LAST_TAG:-}" ]]; then
    VERSION_HEADER="${LAST_TAG#v} - $CURRENT_DATE"
else
    VERSION_HEADER="Unreleased"
fi

# Write changelog
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$VERSION_HEADER]"
    echo ""

    for cat in "Added" "Fixed" "Changed" "Removed" "Security"; do
        content="${ITEMS[$cat]}"
        if [[ -n "$content" ]]; then
            echo "### $cat"
            echo "$content"
            echo ""
        fi
    done

    other="${ITEMS[Other]}"
    if [[ -n "$other" ]]; then
        echo "### Other"
        echo "$other"
        echo ""
    fi

} > "$OUTPUT"

echo "Changelog written to $OUTPUT"
