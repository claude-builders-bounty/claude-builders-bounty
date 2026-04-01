#!/bin/bash

# Generate a structured CHANGELOG.md from git history
# Usage: ./generate-changelog.sh [output-file]

set -e

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
REPO_NAME=$(basename -s .git "$REPO_URL" 2>/dev/null || echo "Repository")

# Get the last tag, or use the first commit if no tags
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo "Error: Could not determine last tag or first commit"
    exit 1
fi

# Get commits since last tag
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%s|%h|%an|%ad" --date=short 2>/dev/null || echo "")
else
    # No tags yet, get all commits
    COMMITS=$(git log --pretty=format:"%s|%h|%an|%ad" --date=short 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
    echo "No new commits since $LAST_TAG"
    exit 0
fi

# Get today's date
TODAY=$(date +%Y-%m-%d)

# Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

# Process each commit
while IFS='|' read -r subject hash author date; do
    # Skip merge commits
    [[ "$subject" =~ ^Merge ]] && continue
    
    # Format: - Description [(hash)](url) by @author
    COMMIT_URL="${REPO_URL%.git}/commit/$hash"
    if [ -z "$REPO_URL" ]; then
        ENTRY="- $subject ($hash) by $author"
    else
        ENTRY="- $subject ([$hash]($COMMIT_URL)) by $author"
    fi
    
    # Categorize based on conventional commit prefixes or keywords
    if [[ "$subject" =~ ^(feat|add|new|implement|introduce): ]] || \
       [[ "$subject" =~ ^(feat|add|new|implement|introduce)\( ]] || \
       [[ "$subject" =~ ^[Aa]dd ]] || \
       [[ "$subject" =~ ^[Ii]mplement ]] || \
       [[ "$subject" =~ ^[Ff]eature ]]; then
        ADDED="$ADDED$ENTRY
"
    elif [[ "$subject" =~ ^(fix|bugfix|hotfix|resolve): ]] || \
         [[ "$subject" =~ ^(fix|bugfix|hotfix|resolve)\( ]] || \
         [[ "$subject" =~ ^[Ff]ix ]] || \
         [[ "$subject" =~ ^[Bb]ug ]] || \
         [[ "$subject" =~ ^[Rr]esolve ]]; then
        FIXED="$FIXED$ENTRY
"
    elif [[ "$subject" =~ ^(change|update|modify|refactor|improve|enhance): ]] || \
         [[ "$subject" =~ ^(change|update|modify|refactor|improve|enhance)\( ]] || \
         [[ "$subject" =~ ^[Uu]pdate ]] || \
         [[ "$subject" =~ ^[Rr]efactor ]] || \
         [[ "$subject" =~ ^[Ii]mprove ]] || \
         [[ "$subject" =~ ^[Cc]hange ]]; then
        CHANGED="$CHANGED$ENTRY
"
    elif [[ "$subject" =~ ^(remove|delete|drop|deprecate): ]] || \
         [[ "$subject" =~ ^(remove|delete|drop|deprecate)\( ]] || \
         [[ "$subject" =~ ^[Rr]emove ]] || \
         [[ "$subject" =~ ^[Dd]elete ]] || \
         [[ "$subject" =~ ^[Dd]rop ]]; then
        REMOVED="$REMOVED$ENTRY
"
    else
        OTHER="$OTHER$ENTRY
"
    fi
done <<< "$COMMITS"

# Generate CHANGELOG
CHANGELOG="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - $TODAY
"

if [ -n "$ADDED" ]; then
    CHANGELOG="$CHANGELOG
### Added
$ADDED"
fi

if [ -n "$CHANGED" ]; then
    CHANGELOG="$CHANGELOG
### Changed
$CHANGED"
fi

if [ -n "$FIXED" ]; then
    CHANGELOG="$CHANGELOG
### Fixed
$FIXED"
fi

if [ -n "$REMOVED" ]; then
    CHANGELOG="$CHANGELOG
### Removed
$REMOVED"
fi

if [ -n "$OTHER" ]; then
    CHANGELOG="$CHANGELOG
### Other
$OTHER"
fi

# Write to file
echo "$CHANGELOG" > "$OUTPUT_FILE"
echo "✅ CHANGELOG generated at $OUTPUT_FILE"
echo ""
echo "Summary:"
echo "  Added:   $(echo -n "$ADDED" | grep -c "^-" || echo 0) commits"
echo "  Changed: $(echo -n "$CHANGED" | grep -c "^-" || echo 0) commits"
echo "  Fixed:   $(echo -n "$FIXED" | grep -c "^-" || echo 0) commits"
echo "  Removed: $(echo -n "$REMOVED" | grep -c "^-" || echo 0) commits"
echo "  Other:   $(echo -n "$OTHER" | grep -c "^-" || echo 0) commits"