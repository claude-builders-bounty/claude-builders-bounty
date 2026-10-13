#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
# Default output: CHANGELOG.md

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo '.')"
cd "$REPO_ROOT"

# Get the last tag (or empty if no tags)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Get commits since last tag (or all commits if no tag)
if [ -n "$LAST_TAG" ]; then
    COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%H|%s|%b" 2>/dev/null || echo "")
    RANGE="$LAST_TAG..HEAD"
else
    COMMITS=$(git log --pretty=format:"%H|%s|%b" 2>/dev/null || echo "")
    RANGE="all commits"
fi

if [ -z "$COMMITS" ]; then
    echo "No commits found."
    exit 0
fi

# Initialize arrays
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Categorize commits
while IFS='|' read -r hash subject body; do
    # Skip empty lines
    [ -z "$hash" ] && continue
    
    # Determine category based on conventional commit prefixes or keywords
    SUBJECT_LOWER=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    
    if echo "$SUBJECT_LOWER" | grep -qE '^(feat|add|new|implement|introduce)'; then
        ADDED+=("- $subject")
    elif echo "$SUBJECT_LOWER" | grep -qE '^(fix|bug|patch|resolve|correct|repair)'; then
        FIXED+=("- $subject")
    elif echo "$SUBJECT_LOWER" | grep -qE '^(remove|delete|drop|deprecate)'; then
        REMOVED+=("- $subject")
    elif echo "$SUBJECT_LOWER" | grep -qE '^(update|change|modify|refactor|improve|enhance|upgrade|bump)'; then
        CHANGED+=("- $subject")
    else
        # Default to Changed
        CHANGED+=("- $subject")
    fi
done <<< "$COMMITS"

# Generate CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    echo ""
    echo "## [Unreleased]"
    echo ""
    echo "Range: $RANGE"
    echo ""
    
    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        echo ""
        for item in "${ADDED[@]}"; do
            echo "$item"
        done
        echo ""
    fi
    
    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        echo ""
        for item in "${FIXED[@]}"; do
            echo "$item"
        done
        echo ""
    fi
    
    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        echo ""
        for item in "${CHANGED[@]}"; do
            echo "$item"
        done
        echo ""
    fi
    
    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        echo ""
        for item in "${REMOVED[@]}"; do
            echo "$item"
        done
        echo ""
    fi
} > "$OUTPUT"

echo "✅ CHANGELOG.md generated at $OUTPUT"
echo "   Range: $RANGE"
echo "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]}"
