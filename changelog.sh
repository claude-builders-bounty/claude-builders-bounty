#!/bin/bash

# Script to generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh

# Get the latest tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

# If no tags exist, use the first commit
if [ -z "$LAST_TAG" ]; then
    LAST_TAG="$(git rev-list --max-parents=0 HEAD)"
    VERSION="0.0.1"
else
    # Get next version number
    MAJOR=$(echo $LAST_TAG | cut -d. -f1)
    MINOR=$(echo $LAST_TAG | cut -d. -f2)
    PATCH=$(echo $LAST_TAG | cut -d. -f3)
    VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
fi

# Create temporary file for changelog
TEMP_CHANGELOG=$(mktemp)

# Add header
echo "# Changelog" > $TEMP_CHANGELOG
echo "" >> $TEMP_CHANGELOG
echo "All notable changes to this project will be documented in this file." >> $TEMP_CHANGELOG
echo "" >> $TEMP_CHANGELOG
echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)," >> $TEMP_CHANGELOG
echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)." >> $TEMP_CHANGELOG
echo "" >> $TEMP_CHANGELOG

# Add unreleased section
echo "## [Unreleased]" >> $TEMP_CHANGELOG
echo "" >> $TEMP_CHANGELOG

# Initialize categories
echo "### Added" >> $TEMP_CHANGELOG
echo "" >> $TEMP_CHANGELOG
echo "### Changed" >> $TEMP_CHANGELOG
echo "" >> $TEMP_CHANGELOG
echo "### Fixed" >> $TEMP_CHANGELOG
echo "" >> $TEMP_CHANGELOG
echo "### Removed" >> $TEMP_CHANGELOG
echo "" >> $TEMP_CHANGELOG

# Get commits since last tag
if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"%H %s")
else
    COMMITS=$(git log $LAST_TAG..HEAD --pretty=format:"%H %s")
fi

# Process each commit
for COMMIT in $COMMITS; do
    HASH=$(echo $COMMIT | cut -d' ' -f1)
    MESSAGE=$(echo $COMMIT | cut -d' ' -f2-)
    
    # Skip merge commits
    if [[ $MESSAGE == "Merge"* ]]; then
        continue
    fi
    
    # Categorize based on commit message
    if [[ $MESSAGE =~ feat(|ure)[\(:] ]]; then
        CATEGORY="Added"
    elif [[ $MESSAGE =~ fix|bug|err|issue ]]; then
        CATEGORY="Fixed"
    elif [[ $MESSAGE =~ refactor|perf|style|test|docs|build|ci|chore ]]; then
        CATEGORY="Changed"
    elif [[ $MESSAGE =~ remov|delet|drop ]]; then
        CATEGORY="Removed"
    else
        CATEGORY="Changed"
    fi
    
    # Add to appropriate category
    sed -i "/### $CATEGORY/a- $MESSAGE (\`$HASH\`)" $TEMP_CHANGELOG
    sed -i "/### $CATEGORY/a" $TEMP_CHANGELOG
done

# Add version section if we have new commits
if [ -n "$COMMITS" ]; then
    echo "" >> $TEMP_CHANGELOG
    echo "## [$VERSION] - $(date +%Y-%m-%d)" >> $TEMP_CHANGELOG
    echo "" >> $TEMP_CHANGELOG
    
    # Copy the unreleased content to the new version section
    sed -n '/## \[Unreleased\]/,/^$/p' $TEMP_CHANGELOG | grep -v "## \[Unreleased\]" >> $TEMP_CHANGELOG
    
    # Clear the unreleased section except for headers
    sed -i '/## \[Unreleased\]/,/^$/ {
        /## \[Unreleased\]/!d
        /^$/d
        /^### Added$/!d
        /^### Added$/a
    }' $TEMP_CHANGELOG
    
    # Add empty line after version section
    echo "" >> $TEMP_CHANGELOG
    
    # Add previous version if it exists
    if [ -n "$LAST_TAG" ]; then
        echo "## [$LAST_TAG] - $(git log -1 --format=%ad --date=format:%Y-%m-%d $LAST_TAG)" >> $TEMP_CHANGELOG
        echo "" >> $TEMP_CHANGELOG
    fi
fi

# Replace CHANGELOG.md with the new content
mv $TEMP_CHANGELOG CHANGELOG.md

echo "CHANGELOG.md has been updated!"
echo "New version: $VERSION"