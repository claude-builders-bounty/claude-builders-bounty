#!/bin/bash
# CHANGELOG Generator
# Automatically generates a structured CHANGELOG.md from git history

set -e

echo "📝 Generating CHANGELOG from git history..."

# Get last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
    echo "📌 Last tag: $LAST_TAG"
    VERSION="v$LAST_TAG"
    REF="$LAST_TAG..HEAD"
else
    echo "📌 No tags found, using all commits"
    VERSION="Unreleased"
    REF="HEAD"
fi

# Get commits
COMMITS=$(git log $REF --pretty=format:%s 2>/dev/null || echo "")
COMMIT_COUNT=$(echo "$COMMITS" | grep -c . || echo "0")
echo "📊 Found $COMMIT_COUNT commits"

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r commit; do
    [ -z "$commit" ] && continue
    
    COMMIT_LOWER=$(echo "$commit" | tr '[:upper:]' '[:lower:]')
    
    if echo "$COMMIT_LOWER" | grep -qE "(add|added|add:|feat:|feature|new|create|implement)"; then
        ADDED="$ADDED- $commit"$'\n'
    elif echo "$COMMIT_LOWER" | grep -qE "(fix|fixed|fix:|bug|bugfix|resolve|correct|patch)"; then
        FIXED="$FIXED- $commit"$'\n'
    elif echo "$COMMIT_LOWER" | grep -qE "(remove|removed|remove:|delete|deleted|deprecate|deprecation)"; then
        REMOVED="$REMOVED- $commit"$'\n'
    else
        CHANGED="$CHANGED- $commit"$'\n'
    fi
done <<< "$COMMITS"

# Build changelog
DATE=$(date +%Y-%m-%d)
CHANGELOG="# Changelog\n\n"
CHANGELOG+="## [$VERSION] - $DATE\n\n"

if [ -n "$ADDED" ]; then
    CHANGELOG+="### Added\n\n$ADDED\n"
fi

if [ -n "$FIXED" ]; then
    CHANGELOG+="### Fixed\n\n$FIXED\n"
fi

if [ -n "$CHANGED" ]; then
    CHANGELOG+="### Changed\n\n$CHANGED\n"
fi

if [ -n "$REMOVED" ]; then
    CHANGELOG+="### Removed\n\n$REMOVED\n"
fi

if [ -z "$ADDED" ] && [ -z "$FIXED" ] && [ -z "$CHANGED" ] && [ -z "$REMOVED" ]; then
    CHANGELOG+="No changes since last release.\n"
fi

# Write to file
echo -e "$CHANGELOG" > CHANGELOG.md

echo "✅ CHANGELOG.md generated successfully!"
echo "📄 Version: $VERSION"
echo "📝 Commits processed: $COMMIT_COUNT"