#!/bin/bash
# Generate CHANGELOG from Git History
# Usage: ./changelog.sh [version]

set -e

# Get the latest tag or start from beginning
LATEST_TAG=$(git tag --sort=-v:refname 2>/dev/null | head -1)

if [ -z "$LATEST_TAG" ]; then
    echo "No tags found. Generating changelog from the beginning..."
    COMMITS=$(git log --pretty=format:"%s" --reverse)
else
    echo "Generating changelog since $LATEST_TAG..."
    COMMITS=$(git log --pretty=format:"%s" "$LATEST_TAG"..HEAD --reverse)
fi

# Categories
declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED
declare -a SECURITY

# Categorize commits
while IFS= read -r commit; do
    lower=$(echo "$commit" | tr '[:upper:]' '[:lower:]')

    if echo "$lower" | grep -qiE '^(feat|add|new|create|implement|introduce|feature)'; then
        ADDED+=("$commit")
    elif echo "$lower" | grep -qiE '^(fix|bug|patch|resolve|correct|repair)'; then
        FIXED+=("$commit")
    elif echo "$lower" | grep -qiE '^(change|update|modify|refactor|improve|enhance)'; then
        CHANGED+=("$commit")
    elif echo "$lower" | grep -qiE '^(remove|delete|drop|deprecate)'; then
        REMOVED+=("$commit")
    elif echo "$lower" | grep -qiE '^(security|vulnerability|cve)'; then
        SECURITY+=("$commit")
    else
        # Default to Changed
        CHANGED+=("$commit")
    fi
done <<< "$COMMITS"

# Generate CHANGELOG.md
VERSION="${1:-Unreleased}"
DATE=$(date +%Y-%m-%d)

cat > CHANGELOG.md << EOF
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [$VERSION] - $DATE

EOF

# Write categories
if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added" >> CHANGELOG.md
    for item in "${ADDED[@]}"; do
        echo "- $item" >> CHANGELOG.md
    done
    echo "" >> CHANGELOG.md
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed" >> CHANGELOG.md
    for item in "${FIXED[@]}"; do
        echo "- $item" >> CHANGELOG.md
    done
    echo "" >> CHANGELOG.md
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed" >> CHANGELOG.md
    for item in "${CHANGED[@]}"; do
        echo "- $item" >> CHANGELOG.md
    done
    echo "" >> CHANGELOG.md
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed" >> CHANGELOG.md
    for item in "${REMOVED[@]}"; do
        echo "- $item" >> CHANGELOG.md
    done
    echo "" >> CHANGELOG.md
fi

if [ ${#SECURITY[@]} -gt 0 ]; then
    echo "### Security" >> CHANGELOG.md
    for item in "${SECURITY[@]}"; do
        echo "- $item" >> CHANGELOG.md
    done
    echo "" >> CHANGELOG.md
fi

echo "✅ CHANGELOG.md generated successfully!"
echo "   Categories: Added(${#ADDED[@]}), Fixed(${#FIXED[@]}), Changed(${#CHANGED[@]}), Removed(${#REMOVED[@]}), Security(${#SECURITY[@]})"
