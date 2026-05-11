#!/bin/bash

# changelog.sh - Automatically generate a structured CHANGELOG.md from git history

# Find the last tag, if none exists, get all commits
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"%s")
    VERSION="Initial Release"
else
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s")
    VERSION="Unreleased (since $LAST_TAG)"
fi

if [ -z "$COMMITS" ]; then
    echo "No commits found."
    exit 0
fi

echo "# CHANGELOG" > CHANGELOG.md
echo "" >> CHANGELOG.md
echo "## $VERSION" >> CHANGELOG.md
echo "" >> CHANGELOG.md

declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED

# Read commits line by line
while IFS= read -r line; do
    # Skip empty lines
    [ -z "$line" ] && continue
    
    if echo "$line" | grep -qiE "^(feat|add)"; then
        ADDED+=("- $line")
    elif echo "$line" | grep -qiE "^(fix|bug|hotfix)"; then
        FIXED+=("- $line")
    elif echo "$line" | grep -qiE "^(remove|del|rm|drop)"; then
        REMOVED+=("- $line")
    else
        CHANGED+=("- $line")
    fi
done <<< "$COMMITS"

# Output Added section
if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added" >> CHANGELOG.md
    printf "%s\n" "${ADDED[@]}" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

# Output Fixed section
if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed" >> CHANGELOG.md
    printf "%s\n" "${FIXED[@]}" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

# Output Changed section
if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed" >> CHANGELOG.md
    printf "%s\n" "${CHANGED[@]}" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

# Output Removed section
if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed" >> CHANGELOG.md
    printf "%s\n" "${REMOVED[@]}" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

echo "CHANGELOG.md generated successfully!"
