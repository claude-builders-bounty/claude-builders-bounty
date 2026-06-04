#!/usr/bin/env bash
# generate-changelog.sh - Generate structured CHANGELOG from git history
# Usage: bash generate-changelog.sh [output_file]
# Outputs: CHANGELOG.md with Added/Fixed/Changed/Removed categories

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "All notable changes to this project are documented in this file." >> "$OUTPUT"
echo "Generated from git history." >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Get the latest tag, or use initial commit if no tags exist
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LATEST_TAG" ]; then
    RANGE="HEAD"
    SECTION="## [Unreleased] - $(date +%Y-%m-%d)"
else
    RANGE="${LATEST_TAG}..HEAD"
    SECTION="## [Unreleased] - $(date +%Y-%m-%d) (since ${LATEST_TAG})"
fi

echo "$SECTION" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Categorize commits by conventional commit prefixes
ADDED=$(git log "$RANGE" --pretty=format:"- %s (%h)" --grep="^feat" --grep="^add" --grep="^new" --all-match="" 2>/dev/null || git log "$RANGE" --pretty=format:"- %s (%h)" --grep="^feat" 2>/dev/null || git log "$RANGE" --pretty=format:"- %s (%h)" -i --grep="^feat\|^add\|^new" 2>/dev/null || echo "")
FIXED=$(git log "$RANGE" --pretty=format:"- %s (%h)" -i --grep="^fix\|^bug\|^hotfix" 2>/dev/null || echo "")
CHANGED=$(git log "$RANGE" --pretty=format:"- %s (%h)" -i --grep="^change\|^update\|^refactor\|^chore\|^perf\|^style\|^docs" 2>/dev/null || echo "")
REMOVED=$(git log "$RANGE" --pretty=format:"- %s (%h)" -i --grep="^remove\|^delete\|^deprecat" 2>/dev/null || echo "")

if [ -n "$ADDED" ]; then
    echo "### Added" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$ADDED" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

if [ -n "$FIXED" ]; then
    echo "### Fixed" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$FIXED" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

if [ -n "$CHANGED" ]; then
    echo "### Changed" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$CHANGED" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

if [ -n "$REMOVED" ]; then
    echo "### Removed" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$REMOVED" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

# If no conventional commits found, just list all commits
if [ -z "$ADDED" ] && [ -z "$FIXED" ] && [ -z "$CHANGED" ] && [ -z "$REMOVED" ]; then
    echo "### Commits" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    git log "$RANGE" --pretty=format:"- %s (%h)" >> "$OUTPUT" 2>/dev/null || echo "- No commits found" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

# Append previous changelog if it exists (skip header)
if [ -f "CHANGELOG.md.orig" ]; then
    echo "---" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    tail -n +7 "CHANGELOG.md.orig" >> "$OUTPUT" 2>/dev/null || true
fi

echo "Changelog generated: $OUTPUT"
