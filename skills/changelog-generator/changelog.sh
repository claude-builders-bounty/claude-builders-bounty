#!/bin/bash
# changelog.sh - Auto-generate CHANGELOG.md from git history
# Usage: ./changelog.sh

set -e

REPO_ROOT="${1:-.}"
LAST_TAG=$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo "No previous tags found. Using all commits." >&2
    COMMIT_RANGE="HEAD"
else
    echo "Generating changelog since $LAST_TAG" >&2
    COMMIT_RANGE="${LAST_TAG}..HEAD"
fi

# Categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

# Parse commits
while IFS= read -r line; do
    [ -z "$line" ] && continue
    msg=$(echo "$line" | sed 's/^[^ ]* //')
    lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    if echo "$lower" | grep -qE '^(feat|add|new|implement|introduce)'; then
        ADDED="${ADDED}- ${msg}\n"
    elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|hotfix)'; then
        FIXED="${FIXED}- ${msg}\n"
    elif echo "$lower" | grep -qE '^(change|update|modify|refactor|improve|enhance|upgrade|deprecat)'; then
        CHANGED="${CHANGED}- ${msg}\n"
    elif echo "$lower" | grep -qE '^(remove|delete|drop|clean|remov)'; then
        REMOVED="${REMOVED}- ${msg}\n"
    else
        OTHER="${OTHER}- ${msg}\n"
    fi
done < <(git -C "$REPO_ROOT" log "$COMMIT_RANGE" --pretty=format:"%h %s" --no-merges)

# Generate CHANGELOG.md
DATE=$(date +%Y-%m-%d)
VERSION=$(git -C "$REPO_ROOT" describe --tags --abbrev=0 2>/dev/null || echo "v$(date +%Y.%m.%d)")

{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$VERSION] - $DATE"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo -e "$ADDED"
        echo ""
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo -e "$FIXED"
        echo ""
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo -e "$CHANGED"
        echo ""
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo -e "$REMOVED"
        echo ""
    fi
    
    if [ -n "$OTHER" ]; then
        echo "### Other"
        echo -e "$OTHER"
        echo ""
    fi
    
} > "$REPO_ROOT/CHANGELOG.md"

echo "✅ CHANGELOG.md generated at $REPO_ROOT/CHANGELOG.md"
