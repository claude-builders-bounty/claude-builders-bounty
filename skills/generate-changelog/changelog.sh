#!/bin/bash

# CHANGELOG Generator
# Usage: ./changelog.sh [output_file]
# Generates a structured CHANGELOG.md from git history

OUTPUT_FILE="${1:-CHANGELOG.md}"

# Check if in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

# Get the latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

# Get commits
if [ -n "$LATEST_TAG" ]; then
    COMMITS=$(git log "$LATEST_TAG"..HEAD --pretty=format:"%s" --no-merges 2>/dev/null)
    VERSION="Unreleased (since $LATEST_TAG)"
else
    COMMITS=$(git log --pretty=format:"%s" --no-merges -100 2>/dev/null)
    VERSION="Unreleased"
fi

# Check if there are any commits
if [ -z "$COMMITS" ]; then
    echo "No commits found since last tag"
    exit 0
fi

# Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# Categorize commits based on conventional commit prefixes
while IFS= read -r commit; do
    # Skip empty lines
    [ -z "$commit" ] && continue
    
    lower=$(echo "$commit" | tr '[:upper:]' '[:lower:]')
    
    # Categorize based on prefix patterns
    if [[ "$lower" =~ ^(feat|feature|add|new)(\(.+\))?: ]] || [[ "$lower" =~ ^\[?\+ ]]; then
        ADDED+="- $commit"$'\n'
    elif [[ "$lower" =~ ^(fix|bugfix|bug|hotfix)(\(.+\))?: ]]; then
        FIXED+="- $commit"$'\n'
    elif [[ "$lower" =~ ^(change|update|refactor|improve|modify|perf)(\(.+\))?: ]]; then
        CHANGED+="- $commit"$'\n'
    elif [[ "$lower" =~ ^(remove|delete|deprecate)(\(.+\))?: ]] || [[ "$lower" =~ ^\[?\- ]]; then
        REMOVED+="- $commit"$'\n'
    else
        # Default to Changed for unrecognized commits
        CHANGED+="- $commit"$'\n'
    fi
done <<< "$COMMITS"

# Backup existing CHANGELOG if present
if [ -f "$OUTPUT_FILE" ]; then
    cp "$OUTPUT_FILE" "${OUTPUT_FILE}.bak"
    echo "✓ Backed up existing $OUTPUT_FILE to ${OUTPUT_FILE}.bak"
fi

# Generate CHANGELOG content
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$VERSION]"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        printf '%s' "$ADDED"
        echo ""
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        printf '%s' "$FIXED"
        echo ""
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        printf '%s' "$CHANGED"
        echo ""
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        printf '%s' "$REMOVED"
        echo ""
    fi
} > "$OUTPUT_FILE"

# Count commits
COMMIT_COUNT=$(echo "$COMMITS" | wc -l)
echo "✓ Generated $OUTPUT_FILE with $COMMIT_COUNT commits"
echo ""
echo "Preview:"
echo "--------"
head -20 "$OUTPUT_FILE"