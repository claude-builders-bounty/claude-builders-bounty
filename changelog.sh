#!/bin/bash
# changelog.sh - Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh

set -euo pipefail

REPO_URL=$(git remote get-url origin 2>/dev/null || echo "unknown")
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
OUTPUT_FILE="CHANGELOG.md"

# Get date
DATE=$(date +%Y-%m-%d)

# Get commits since last tag (or all if no tags)
if [ -n "$LATEST_TAG" ]; then
    COMMITS=$(git log "$LATEST_TAG"..HEAD --pretty=format:"%s")
    HEADER_TAG="$LATEST_TAG → HEAD"
else
    COMMITS=$(git log --pretty=format:"%s")
    HEADER_TAG="Initial Release"
fi

# Categorize commits
ADDED=$(echo "$COMMITS" | grep -iE '^(feat|add|new|introduce|implement)' || true)
FIXED=$(echo "$COMMITS" | grep -iE '^(fix|bug|repair|correct|resolve|hotfix|patch|security)' || true)
CHANGED=$(echo "$COMMITS" | grep -iE '^(change|update|modify|refactor|improve|enhance|perf|optimize|docs|style|test|chore)' || true)
REMOVED=$(echo "$COMMITS" | grep -iE '^(remove|delete|drop|deprecat|clean)' || true)
UNCATEGORIZED=$(echo "$COMMITS" | while read line; do
    if ! echo "$line" | grep -qiE '^(feat|add|new|introduce|implement|fix|bug|repair|correct|resolve|hotfix|patch|security|change|update|modify|refactor|improve|enhance|perf|optimize|docs|style|test|chore|remove|delete|drop|deprecat|clean|merge|bump|release)'; then
        echo "$line"
    fi
done || true)

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$HEADER_TAG] - $DATE"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo "$ADDED" | while read line; do
            [ -n "$line" ] && echo "- $line"
        done
        echo ""
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo "$FIXED" | while read line; do
            [ -n "$line" ] && echo "- $line"
        done
        echo ""
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo "$CHANGED" | while read line; do
            [ -n "$line" ] && echo "- $line"
        done
        echo ""
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo "$REMOVED" | while read line; do
            [ -n "$line" ] && echo "- $line"
        done
        echo ""
    fi
    
    if [ -n "$UNCATEGORIZED" ]; then
        echo "### Other"
        echo "$UNCATEGORIZED" | while read line; do
            [ -n "$line" ] && echo "- $line"
        done
        echo ""
    fi
} > "$OUTPUT_FILE"

echo "✅ CHANGELOG.md generated successfully!"
echo "   Output: $OUTPUT_FILE"
echo "   Range: $HEADER_TAG"
echo "   Date: $DATE"
