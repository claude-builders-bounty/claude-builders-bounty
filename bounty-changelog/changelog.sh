#!/bin/bash
#
# Claude Code Skill: Generate CHANGELOG from git history
# Bounty: $50 - claude-builders-bounty #1
#

set -e

# Configuration
OUTPUT_FILE="${OUTPUT_FILE:-CHANGELOG.md}"
REPO_DIR="${REPO_DIR:-.}"

cd "$REPO_DIR"

# Get the latest tag, or use initial commit if no tags
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

# Get commits since last tag
COMMITS=$(git log $LATEST_TAG..HEAD --pretty=format:"%s" --no-merges 2>/dev/null || git log --pretty=format:"%s" --no-merges)

if [ -z "$COMMITS" ]; then
    echo "No new commits since last tag."
    exit 0
fi

# Version from tag or "Unreleased"
VERSION=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/v//' || echo "Unreleased")
DATE=$(date +%Y-%m-%d)

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r commit; do
    # Skip empty lines
    [ -z "$commit" ] && continue
    
    # Categorize based on prefix
    case "$commit" in
        feat:*|add:*|feature:*)
            ADDED="$ADDED\n- $(echo "$commit" | sed 's/^[^:]*://')"
            ;;
        fix:*|bugfix:*|hotfix:*)
            FIXED="$FIXED\n- $(echo "$commit" | sed 's/^[^:]*://')"
            ;;
        change:*|update:*|refactor:*|improve:*)
            CHANGED="$CHANGED\n- $(echo "$commit" | sed 's/^[^:]*://')"
            ;;
        remove:*|delete:*|deprecate:*)
            REMOVED="$REMOVED\n- $(echo "$commit" | sed 's/^[^:]*://')"
            ;;
        *)
            # Default to Changed
            CHANGED="$CHANGED\n- $commit"
            ;;
    esac
done <<< "$COMMITS"

# Generate CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$VERSION] - $Date"
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
    
    # Append existing changelog if exists
    if [ -f "$OUTPUT_FILE" ] && [ "$OUTPUT_FILE" != "CHANGELOG.md" ]; then
        echo ""
        cat "$OUTPUT_FILE"
    fi
    
} > "$OUTPUT_FILE"

echo "✅ CHANGELOG generated: $OUTPUT_FILE"