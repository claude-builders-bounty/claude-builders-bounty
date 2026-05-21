#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
# Default output: CHANGELOG.md

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo '.')"

# Get the latest tag, or fall back to initial commit
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LATEST_TAG" ]; then
    RANGE="HEAD"
    echo "No tags found, using full history"
else
    RANGE="${LATEST_TAG}..HEAD"
    echo "Generating changelog since ${LATEST_TAG}"
fi

# Collect commits
COMMITS=$(git log "$RANGE" --pretty=format:"%H|%s|%an|%ad" --date=short 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    echo "No commits found in range"
    exit 0
fi

# Categorize commits by conventional commit prefix
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS='|' read -r hash subject author date; do
    # Skip merge commits
    if echo "$subject" | grep -qiE "^merge "; then
        continue
    fi
    
    SHORT_HASH="${hash:0:7}"
    ENTRY="- ${subject} (\`${SHORT_HASH}\`) — ${author} (${date})"
    
    # Categorize by prefix (case-insensitive)
    LOWER_SUBJECT=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    
    if echo "$LOWER_SUBJECT" | grep -qE "^(feat|add|new|create|implement|introduce)"; then
        ADDED="${ADDED}\n${ENTRY}"
    elif echo "$LOWER_SUBJECT" | grep -qE "^(fix|bugfix|patch|resolve|correct)"; then
        FIXED="${FIXED}\n${ENTRY}"
    elif echo "$LOWER_SUBJECT" | grep -qE "^(remove|delete|deprecate|drop|eliminate)"; then
        REMOVED="${REMOVED}\n${ENTRY}"
    elif echo "$LOWER_SUBJECT" | grep -qE "^(refactor|change|update|modify|improve|perf|optimize|style|chore|build|ci|docs|test)"; then
        CHANGED="${CHANGED}\n${ENTRY}"
    else
        OTHER="${OTHER}\n${ENTRY}"
    fi
done <<< "$COMMITS"

# Build output
{
    echo "# Changelog"
    echo ""
    
    if [ -n "$LATEST_TAG" ]; then
        echo "## [Unreleased] — since ${LATEST_TAG}"
    else
        echo "## [Unreleased]"
    fi
    echo ""
    echo "_Generated on $(date +%Y-%m-%d)_"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo -e "$ADDED"
        echo ""
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo -e "$FIXED"
        echo ""
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo -e "$CHANGED"
        echo ""
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo -e "$REMOVED"
        echo ""
    fi
    
    if [ -n "$OTHER" ]; then
        echo "### Other"
        echo -e "$OTHER"
        echo ""
    fi
} > "$OUTPUT"

echo "✓ Changelog written to ${OUTPUT}"
echo "  Commits processed: $(echo "$COMMITS" | wc -l)"
