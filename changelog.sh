#!/usr/bin/env bash

# changelog.sh - Generate a CHANGELOG.md from git history since the last tag

set -euo pipefail

# Function to print usage
usage() {
    echo "Usage: $0 [-o output_file]"
    echo "  -o output_file: Write changelog to output_file (default: CHANGELOG.md)"
    exit 1
}

# Default output file
OUTPUT_FILE="CHANGELOG.md"

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        -o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Get the latest tag (by version order, excluding prereleases if possible)
# We'll use `git tag --sort=-version:refname` and take the first one.
LATEST_TAG=$(git tag --sort=-version:refname | head -n1 || true)

if [ -z "$LATEST_TAG" ]; then
    # No tags, compare to the initial commit
    echo "No tags found, comparing to the initial commit."
    BASE="HEAD"
else
    echo "Latest tag: $LATEST_TAG"
    BASE="$LATEST_TAG..HEAD"
fi

# Get commits since the base
# We'll get the commit hash and subject
COMMITS=$(git log $BASE --pretty=format:"%h %s" --no-merges)

# Initialize categories
declare -A categories
categories["Added"]=""
categories["Fixed"]=""
categories["Changed"]=""
categories["Removed"]=""

# Process each commit
while IFS= read -r line; do
    # Skip empty lines
    [ -z "$line" ] && continue

    # Extract hash and subject
    hash=$(echo "$line" | cut -d' ' -f1)
    subject=$(echo "$line" | cut -d' ' -f2-)

    # Convert subject to lowercase for matching
    subject_lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

    # Categorize based on keywords in the subject
    if [[ "$subject_lower" =~ ^(feat|add|new) ]]; then
        categories["Added"]+="- $hash: $subject
"
    elif [[ "$subject_lower" =~ ^(fix|bug|patch) ]]; then
        categories["Fixed"]+="- $hash: $subject
"
    elif [[ "$subject_lower" =~ ^(remove|delete) ]]; then
        categories["Removed"]+="- $hash: $subject
"
    else
        # Default to Changed for everything else (including update, change, modify, refactor, perf, etc.)
        categories["Changed"]+="- $hash: $subject
"
    fi
done <<< "$COMMITS"

# Get current date for the header
CURRENT_DATE=$(date +%Y-%m-%d)

# Write the changelog
{
    echo "# Changelog"
    echo ""
    echo "## [Unreleased] - $CURRENT_DATE"
    echo ""

    for category in Added Fixed Changed Removed; do
        echo "### $category"
        echo ""
        if [ -z "${categories[$category]}" ]; then
            echo "*No changes*"
            echo ""
        else
            echo -e "${categories[$category]}"
            echo ""
        fi
    done
} > "$OUTPUT_FILE"

echo "Changelog generated: $OUTPUT_FILE"