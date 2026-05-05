#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history.
# Usage: ./changelog.sh [REPO_PATH]
#   REPO_PATH defaults to current directory.

set -euo pipefail

REPO="${1:-$(pwd)}"
cd "$REPO"

OUTPUT="CHANGELOG.md"

# Get the latest tag (or "initial commit" as fallback)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
    # No tags yet -- use the first commit
    LAST_TAG=$(git rev-list --max-parents=0 HEAD)
fi

# Get today's date in YYYY-MM-DD format
TODAY=$(date +%Y-%m-%d)

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## [$LAST_TAG] - $TODAY" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Fetch commits since last tag
COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%s" 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    echo "_No commits since $LAST_TAG._" >> "$OUTPUT"
    echo "CHANGELOG.md generated (empty)."
    exit 0
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS= read -r line; do
    # Skip empty lines
    [ -z "$line" ] && continue

    # Categorize by conventional commit prefix
    if echo "$line" | grep -qiE "^(add|feat|new|implement|create|introduce)\b"; then
        ADDED+=("- $line")
    elif echo "$line" | grep -qiE "^(fix|bug|patch|resolve|correct|repair)\b"; then
        FIXED+=("- $line")
    elif echo "$line" | grep -qiE "^(remove|delete|drop|deprecate)\b"; then
        REMOVED+=("- $line")
    else
        CHANGED+=("- $line")
    fi
done <<< "$COMMITS"

# Output sections
if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added" >> "$OUTPUT"
    for entry in "${ADDED[@]}"; do
        echo "$entry" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed" >> "$OUTPUT"
    for entry in "${FIXED[@]}"; do
        echo "$entry" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed" >> "$OUTPUT"
    for entry in "${CHANGED[@]}"; do
        echo "$entry" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed" >> "$OUTPUT"
    for entry in "${REMOVED[@]}"; do
        echo "$entry" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
fi

echo "CHANGELOG.md generated successfully."
echo "Commits categorized: Added=${#ADDED[@]}, Fixed=${#FIXED[@]}, Changed=${#CHANGED[@]}, Removed=${#REMOVED[@]}"
