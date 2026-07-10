#!/bin/bash
# CHANGELOG Generator - Generates structured CHANGELOG.md from git history
# Usage: bash changelog.sh [REPO_PATH]

set -e

REPO_PATH="${1:-.}"
OUTPUT="CHANGELOG.md"

LAST_TAG=$(git -C "$REPO_PATH" describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git -C "$REPO_PATH" log --oneline)
else
    COMMITS=$(git -C "$REPO_PATH" log --oneline "$LAST_TAG"..HEAD)
fi

if [ -z "$COMMITS" ]; then
    echo "# CHANGELOG" > "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "No new changes since last tag." >> "$OUTPUT"
    exit 0
fi

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

while IFS= read -r line; do
    msg="${line#[0-9a-f]* }"
    lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    if [[ "$lower" =~ ^add ]]; then
        ADDED+=("- $msg")
    elif [[ "$lower" =~ ^fix ]]; then
        FIXED+=("- $msg")
    elif [[ "$lower" =~ ^remov ]]; then
        REMOVED+=("- $msg")
    elif [[ "$lower" =~ ^(update|change|refactor|improve|bump) ]]; then
        CHANGED+=("- $msg")
    else
        CHANGED+=("- $msg")
    fi
done <<< "$COMMITS"

{
    echo "# CHANGELOG"
    echo ""
    echo "## [Unreleased]"
    echo ""
    if [ ${#ADDED[@]} -gt 0 ]; then echo "### Added"; printf '%s\n' "${ADDED[@]}"; echo ""; fi
    if [ ${#CHANGED[@]} -gt 0 ]; then echo "### Changed"; printf '%s\n' "${CHANGED[@]}"; echo ""; fi
    if [ ${#FIXED[@]} -gt 0 ]; then echo "### Fixed"; printf '%s\n' "${FIXED[@]}"; echo ""; fi
    if [ ${#REMOVED[@]} -gt 0 ]; then echo "### Removed"; printf '%s\n' "${REMOVED[@]}"; echo ""; fi
} > "$OUTPUT"

echo "Generated $OUTPUT"
