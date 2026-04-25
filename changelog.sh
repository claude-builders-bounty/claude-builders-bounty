#!/bin/bash
# Generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [output_file] [since_tag]

set -e

OUTPUT_FILE="${1:-CHANGELOG.md}"
SINCE_TAG="${2:-}"

echo "🔍 Generating changelog..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Get the last tag if not specified
if [ -z "$SINCE_TAG" ]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Get commits
if [ -n "$SINCE_TAG" ]; then
    echo "📋 Getting commits since $SINCE_TAG..."
    COMMITS=$(git log "$SINCE_TAG"..HEAD --pretty=format:"%H|%s|%ad" --date=short)
else
    echo "📋 Getting all commits..."
    COMMITS=$(git log --pretty=format:"%H|%s|%ad" --date=short)
fi

if [ -z "$COMMITS" ]; then
    echo "⚠️  No commits found"
    exit 0
fi

# Generate changelog
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$(date +%Y.%m.%d)] - $(date +%Y-%m-%d)"
    echo ""
    
    # Categorize commits
    ADDED=$(echo "$COMMITS" | grep -iE "(feat|add|new|introduce|create|implement)" || true)
    FIXED=$(echo "$COMMITS" | grep -iE "(fix|bug|hotfix|resolve|correct|patch)" || true)
    CHANGED=$(echo "$COMMITS" | grep -iE "(change|update|modify|refactor|improve|upgrade)" || true)
    REMOVED=$(echo "$COMMITS" | grep -iE "(remove|delete|drop|deprecate|clean)" || true)
    
    # Output categories
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo "$ADDED" | while IFS='|' read -r hash message date; do
            echo "- $message (${hash:0:7})"
        done
        echo ""
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo "$CHANGED" | while IFS='|' read -r hash message date; do
            echo "- $message (${hash:0:7})"
        done
        echo ""
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo "$FIXED" | while IFS='|' read -r hash message date; do
            echo "- $message (${hash:0:7})"
        done
        echo ""
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo "$REMOVED" | while IFS='|' read -r hash message date; do
            echo "- $message (${hash:0:7})"
        done
        echo ""
    fi
    
    echo "---"
    echo ""
    echo "*This changelog was automatically generated from git history.*"
    echo ""
} > "$OUTPUT_FILE"

echo "✅ Changelog generated: $OUTPUT_FILE"
echo "📊 Total commits: $(echo "$COMMITS" | wc -l)"
