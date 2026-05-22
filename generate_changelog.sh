#!/usr/bin/env bash

# generate_changelog.sh
# Automates CHANGELOG generation based on conventional commits since the last tag.

set -e

# Get the latest tag or the first commit if no tags exist
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
NEXT_VERSION=${1:-"Unreleased"}

echo "# Changelog"
echo ""
echo "## [$NEXT_VERSION] - $(date +%Y-%m-%d)"
echo ""

# Declare categories
declare -A CATEGORIES
CATEGORIES=(
    ["Added"]="feat"
    ["Fixed"]="fix"
    ["Changed"]="refactor|perf"
    ["Removed"]="revert"
)

# Fetch commits
COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s (%h)")

for CATEGORY in "${!CATEGORIES[@]}"; do
    PATTERN="${CATEGORIES[$CATEGORY]}"
    
    # Filter commits by conventional commit prefix
    MATCHES=$(echo "$COMMITS" | grep -E "^($PATTERN)(\([a-z-]+\))?:" || true)
    
    if [ ! -z "$MATCHES" ]; then
        echo "### $CATEGORY"
        # Format the commit message as a bullet point list
        echo "$MATCHES" | sed -E 's/^[a-z]+(\([a-z-]+\))?: /- /'
        echo ""
    fi
done
