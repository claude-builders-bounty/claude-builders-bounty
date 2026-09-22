#!/bin/bash

# changelog.sh - Generates a structured CHANGELOG.md from git history

set -e

# 1. Determine the range of commits
# Get the latest tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Generating changelog from all commits."
    RANGE="HEAD"
    VERSION="Unreleased"
else
    echo "Generating changelog since $LAST_TAG"
    RANGE="$LAST_TAG..HEAD"
    VERSION="Unreleased (since $LAST_TAG)"
fi

# 2. Create temporary files for categories
ADDED=$(mktemp)
FIXED=$(mktemp)
CHANGED=$(mktemp)
REMOVED=$(mktemp)

# Ensure cleanup on exit
trap 'rm -f "$ADDED" "$FIXED" "$CHANGED" "$REMOVED"' EXIT

# 3. Parse commits and categorize
# We use a while loop to read each commit message line by line
# We use --pretty=format:"%s" to get only the subject line
git log "$RANGE" --pretty=format:"%s" | while read -r line; do
    [ -z "$line" ] && continue

    # Convert to lowercase for pattern matching
    lower_line=$(echo "$line" | tr '[:upper:]' '[:lower:]')

    # Categorization logic based on common prefixes (Conventional Commits style)
    if [[ "$lower_line" =~ ^feat|^add ]]; then
        echo "- $line" >> "$ADDED"
    elif [[ "$lower_line" =~ ^fix ]]; then
        echo "- $line" >> "$FIXED"
    elif [[ "$lower_line" =~ ^refactor|^perf|^style|^docs|^chore|^build|^ci|^update ]]; then
        echo "- $line" >> "$CHANGED"
    elif [[ "$lower_line" =~ ^remove|^delete|^drop|^del ]]; then
        echo "- $line" >> "$REMOVED"
    else
        # Fallback for commits that don't follow convention
        echo "- $line" >> "$CHANGED"
    fi
done

# 4. Construct the CHANGELOG.md file
CHANGELOG_TMP=$(mktemp)
trap 'rm -f "$ADDED" "$FIXED" "$CHANGED" "$REMOVED" "$CHANGELOG_TMP"' EXIT

{
    echo "# Changelog"
    echo ""
    echo "## $VERSION"
    echo ""

    if [ -s "$ADDED" ]; then
        echo "### Added"
        cat "$ADDED"
        echo ""
    fi

    if [ -s "$FIXED" ]; then
        echo "### Fixed"
        cat "$FIXED"
        echo ""
    fi

    if [ -s "$CHANGED" ]; then
        echo "### Changed"
        cat "$CHANGED"
        echo ""
    fi

    if [ -s "$REMOVED" ]; then
        echo "### Removed"
        cat "$REMOVED"
        echo ""
    fi
} > "$CHANGELOG_TMP"

mv "$CHANGELOG_TMP" CHANGELOG.md

echo "✅ CHANGELOG.md has been generated successfully."
