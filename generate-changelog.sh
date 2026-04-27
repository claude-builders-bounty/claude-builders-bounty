#!/bin/bash
# 💰 Generate CHANGELOG.md from git history
# Usage: ./generate-changelog.sh [output_file]
# Default output: CHANGELOG.md

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_DIR="${2:-.}"

cd "$REPO_DIR"

# Check if it's a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

# Get project name
PROJECT_NAME=$(basename "$(git rev-parse --show-toplevel)" 2>/dev/null || echo "Project")

# Get the latest tag (or use first commit)
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

echo "🔍 Generating CHANGELOG for: $PROJECT_NAME"
echo "📦 Latest tag: ${LATEST_TAG:-none}"

# Determine commit range
if [ -n "$LATEST_TAG" ]; then
    COMMITS=$(git log "$LATEST_TAG"..HEAD --oneline 2>/dev/null || echo "")
else
    COMMITS=$(git log --oneline 2>/dev/null | tail -r | head -1 | cut -d' ' -f1)
    if [ -n "$COMMITS" ]; then
        COMMITS=$(git log --oneline 2>/dev/null)
    fi
fi

# Categorize commits
ADDED=$(git log --oneline ${LATEST_TAG:+$LATEST_TAG..}HEAD --grep="^feat" --grep="^add" --grep="^feature" --regexp-ignore-case 2>/dev/null || echo "")
FIXED=$(git log --oneline ${LATEST_TAG:+$LATEST_TAG..}HEAD --grep="^fix" --grep="^bug" --grep="^hotfix" --regexp-ignore-case 2>/dev/null || echo "")
CHANGED=$(git log --oneline ${LATEST_TAG:+$LATEST_TAG..}HEAD --grep="^refactor" --grep="^update" --grep="^change" --regexp-ignore-case 2>/dev/null || echo "")
REMOVED=$(git log --oneline ${LATEST_TAG:+$LATEST_TAG..}HEAD --grep="^remove" --grep="^delete" --grep="^drop" --regexp-ignore-case 2>/dev/null || echo "")

# Fallback: categorize all commits
if [ -z "$ADDED$FIXED$CHANGED$REMOVED" ]; then
    ALL_COMMITS=$(git log --oneline ${LATEST_TAG:+$LATEST_TAG..}HEAD 2>/dev/null | head -50)
    ADDED=$(echo "$ALL_COMMITS" | grep -iE "add|feat|new|create|implement|init")
    FIXED=$(echo "$ALL_COMMITS" | grep -iE "fix|bug|patch|correct|resolve")
    CHANGED=$(echo "$ALL_COMMITS" | grep -iE "update|change|refactor|improve|migrate|upgrade")
    REMOVED=$(echo "$ALL_COMMITS" | grep -iE "remove|delete|drop|clean|deprecate")
fi

# Generate CHANGELOG
{
    echo "# Changelog"
    echo
    echo "## [Unreleased]"
    echo
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo "$ADDED" | while IFS= read -r line; do
            [ -n "$line" ] && echo "- $line"
        done
        echo
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo "$FIXED" | while IFS= read -r line; do
            [ -n "$line" ] && echo "- $line"
        done
        echo
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo "$CHANGED" | while IFS= read -r line; do
            [ -n "$line" ] && echo "- $line"
        done
        echo
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo "$REMOVED" | while IFS= read -r line; do
            [ -n "$line" ] && echo "- $line"
        done
        echo
    fi
    
    # Include previous tags
    echo "---"
    echo
    for TAG in $(git tag --sort=-creatordate 2>/dev/null | head -5); do
        TAG_DATE=$(git log -1 --format="%ai" "$TAG" 2>/dev/null | cut -d' ' -f1)
        echo "## [$TAG] - $TAG_DATE"
        git log --oneline "$TAG"..$(git tag --sort=-creatordate | grep -A1 "$TAG" | tail -1) 2>/dev/null | head -10 | while IFS= read -r line; do
            echo "- $line"
        done
        echo
    done
    
} > "$OUTPUT"

echo "✅ CHANGELOG generated: $OUTPUT"
echo "📊 $(git rev-list ${LATEST_TAG:+$LATEST_TAG..}HEAD --count 2>/dev/null || echo '0') commits documented"
