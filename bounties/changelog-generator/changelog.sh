#!/bin/bash

# Changelog Generator - Generates structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since TAG] [--output FILE]

set -e

OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""

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
        -h|--help)
            echo "Usage: bash changelog.sh [--since TAG] [--output FILE]"
            echo ""
            echo "Options:"
            echo "  --since TAG    Generate changelog since this tag (default: last tag)"
            echo "  --output FILE  Output file (default: CHANGELOG.md)"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

if [ -z "$SINCE_TAG" ]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -z "$SINCE_TAG" ]; then
    echo "No tags found. Generating changelog from all commits..."
    COMMIT_RANGE="HEAD"
else
    echo "Generating changelog since $SINCE_TAG..."
    COMMIT_RANGE="$SINCE_TAG..HEAD"
fi

CURRENT_DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --always 2>/dev/null || echo "Unreleased")

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

categorize_commit() {
    local msg="$1"
    local lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    if echo "$lower_msg" | grep -qE "^(feat|add|new|create|implement|introduce)"; then
        ADDED="$ADDED\n- $msg"
    elif echo "$lower_msg" | grep -qE "^(fix|bug|patch|resolve|close|correct)"; then
        FIXED="$FIXED\n- $msg"
    elif echo "$lower_msg" | grep -qE "^(remove|delete|drop|deprecate)"; then
        REMOVED="$REMOVED\n- $msg"
    else
        CHANGED="$CHANGED\n- $msg"
    fi
}

while IFS= read -r line; do
    if [ -n "$line" ]; then
        categorize_commit "$line"
    fi
done < <(git log "$COMMIT_RANGE" --pretty=format:"%s" 2>/dev/null || git log --pretty=format:"%s")

{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$VERSION] - $CURRENT_DATE"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo -e "$ADDED" | grep -v '^$'
        echo ""
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo -e "$FIXED" | grep -v '^$'
        echo ""
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo -e "$CHANGED" | grep -v '^$'
        echo ""
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo -e "$REMOVED" | grep -v '^$'
        echo ""
    fi
} > "$OUTPUT_FILE"

echo "Changelog generated: $OUTPUT_FILE"
