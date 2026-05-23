#!/bin/bash
# generate-changelog.sh - Generate structured CHANGELOG.md from git history
# Usage: ./generate-changelog.sh [since-tag] [output-file]
# Default: fetches since last tag, outputs to CHANGELOG.md

set -euo pipefail

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

# Get the last tag, or use the first commit if no tags exist
SINCE_TAG=${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "")}
if [ -z "$SINCE_TAG" ]; then
    SINCE_TAG=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
    if [ -z "$SINCE_TAG" ]; then
        echo "Error: Could not determine start point (no tags and no commits)"
        exit 1
    fi
    echo "No tags found, using first commit: $SINCE_TAG"
fi

OUTPUT=${2:-CHANGELOG.md}

# Get commits since tag with full message and author info
# Format: hash|author|date|subject
COMMITS=$(git log "$SINCE_TAG"..HEAD --pretty=format:"%h|%an|%ad|%s" --date=short --no-merges 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    echo "No new commits since $SINCE_TAG"
    exit 0
fi

# Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

# Function to categorize commit based on conventional commit format
categorize_commit() {
    local subject="$1"
    local lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    
    # Check for conventional commit format: type: message or type(scope): message
    # Added category
    if echo "$lower_subject" | grep -qiE '^(feat|feature|add|new)[(:\s]'; then
        echo "added"
        return
    fi
    
    # Fixed category
    if echo "$lower_subject" | grep -qiE '^(fix|bugfix|bug|hotfix|patch)[(:\s]'; then
        echo "fixed"
        return
    fi
    
    # Changed category
    if echo "$lower_subject" | grep -qiE '^(chore|refactor|update|improve|style|perf|optimize|docs|test|ci|build)[(:\s]'; then
        echo "changed"
        return
    fi
    
    # Removed category
    if echo "$lower_subject" | grep -qiE '^(remove|delete|drop|deprecat)[(:\s]'; then
        echo "removed"
        return
    fi
    
    # Check for keywords anywhere in the message
    if echo "$lower_subject" | grep -qiE '\b(add|implement|create|introduce|support)\b'; then
        echo "added"
        return
    fi
    
    if echo "$lower_subject" | grep -qiE '\b(fix|bug|repair|correct|resolve|patch)\b'; then
        echo "fixed"
        return
    fi
    
    if echo "$lower_subject" | grep -qiE '\b(update|upgrade|modify|change|refactor|improve|optimize|enhance)\b'; then
        echo "changed"
        return
    fi
    
    if echo "$lower_subject" | grep -qiE '\b(remove|delete|drop|deprecat|clean|cleanup)\b'; then
        echo "removed"
        return
    fi
    
    echo "other"
}

# Process each commit
while IFS='|' read -r hash author date subject; do
    # Skip empty lines
    [ -z "$subject" ] && continue
    
    category=$(categorize_commit "$subject")
    
    # Clean up the subject - remove conventional commit prefix if present
    clean_subject="$subject"
    if echo "$subject" | grep -qiE '^(feat|feature|fix|bugfix|bug|chore|refactor|update|improve|style|perf|optimize|docs|test|ci|build|remove|delete|drop|add|new|patch|hotfix)(\([^)]*\))?:\s*'; then
        clean_subject=$(echo "$subject" | sed -E 's/^(feat|feature|fix|bugfix|bug|chore|refactor|update|improve|style|perf|optimize|docs|test|ci|build|remove|delete|drop|add|new|patch|hotfix)(\([^)]*\))?:\s*//i')
    fi
    
    # Capitalize first letter
    clean_subject=$(echo "$clean_subject" | sed 's/^./\u&/')
    
    # Get repo URL for commit links
    repo_url=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]\([^/]*\)\/\([^/]*\).*/\1\/\2/' || echo "user/repo")
    
    entry="- $clean_subject ([$hash](https://github.com/$repo_url/commit/$hash)) by $author"
    
    case "$category" in
        added)
            ADDED="$entry
$ADDED"
            ;;
        fixed)
            FIXED="$entry
$FIXED"
            ;;
        changed)
            CHANGED="$entry
$CHANGED"
            ;;
        removed)
            REMOVED="$entry
$REMOVED"
            ;;
        other)
            OTHER="$entry
$OTHER"
            ;;
    esac
done <<< "$COMMITS"

# Generate the changelog content
CHANGELOG_CONTENT="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - $(date +%Y-%m-%d)
"

if [ -n "$ADDED" ]; then
    CHANGELOG_CONTENT="$CHANGELOG_CONTENT
### Added
$ADDED"
fi

if [ -n "$FIXED" ]; then
    CHANGELOG_CONTENT="$CHANGELOG_CONTENT
### Fixed
$FIXED"
fi

if [ -n "$CHANGED" ]; then
    CHANGELOG_CONTENT="$CHANGELOG_CONTENT
### Changed
$CHANGED"
fi

if [ -n "$REMOVED" ]; then
    CHANGELOG_CONTENT="$CHANGELOG_CONTENT
### Removed
$REMOVED"
fi

if [ -n "$OTHER" ]; then
    CHANGELOG_CONTENT="$CHANGELOG_CONTENT
### Other
$OTHER"
fi

# Check if CHANGELOG.md already exists and preserve previous entries
if [ -f "$OUTPUT" ] && [ "$OUTPUT" = "CHANGELOG.md" ]; then
    # Extract existing content (everything after the first version header)
    existing=$(tail -n +10 "$OUTPUT" 2>/dev/null || echo "")
    if [ -n "$existing" ]; then
        CHANGELOG_CONTENT="$CHANGELOG_CONTENT
$existing"
    fi
fi

# Write to output file
echo "$CHANGELOG_CONTENT" > "$OUTPUT"

echo "✅ CHANGELOG written to $OUTPUT"
echo "   Since: $SINCE_TAG"
echo "   Commits processed: $(echo "$COMMITS" | wc -l)"
