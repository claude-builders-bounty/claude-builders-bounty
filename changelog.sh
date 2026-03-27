#!/bin/bash

# Get the last git tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

# If no tag exists, get the first commit
if [ -z "$LAST_TAG" ]; then
    LAST_TAG=$(git rev-list --max-parents=0 HEAD)
fi

echo "Generating CHANGELOG since $LAST_TAG..."

# Prepare the header
echo "# CHANGELOG" > CHANGELOG.md
echo "Generated on $(date)" >> CHANGELOG.md
echo "" >> CHANGELOG.md

# Function to fetch and format commits
format_commits() {
    local category=$1
    local pattern=$2
    local commits=$(git log "$LAST_TAG..HEAD" --oneline --grep="$pattern" -i --format="- %s (%h)")
    if [ ! -z "$commits" ]; then
        echo "### $category" >> CHANGELOG.md
        echo "$commits" >> CHANGELOG.md
        echo "" >> CHANGELOG.md
    fi
}

# Add categories
format_commits "Added" "add\|feat"
format_commits "Fixed" "fix\|bug"
format_commits "Changed" "change\|update\|refactor"
format_commits "Removed" "remove\|delete"

echo "CHANGELOG.md generated successfully."
