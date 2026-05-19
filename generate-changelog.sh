#!/usr/bin/env bash
# generate-changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [since_tag]

set -euo pipefail

SINCE_TAG="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo '')}"
OUTPUT="CHANGELOG.md"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "project")

# Get today's date
TODAY=$(date +%Y-%m-%d)

# Determine version: if a tag exists, use commits since it. Otherwise "Unreleased".
if [ -n "$SINCE_TAG" ]; then
    RANGE="${SINCE_TAG}..HEAD"
    VERSION="$SINCE_TAG → HEAD"
else
    RANGE=""
    VERSION="Unreleased"
fi

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## [$VERSION] — $TODAY" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Fetch commits
if [ -n "$RANGE" ]; then
    COMMITS=$(git log "$RANGE" --pretty=format:"%s" 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%s" 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
    echo "_No commits found._" >> "$OUTPUT"
    echo "✅ CHANGELOG.md generated (empty)"
    exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    # Strip conventional commit prefix if present
    MSG=$(echo "$line" | sed -E 's/^[a-z]+(\([^)]*\))?!?: //')
    
    # Categorize
    if echo "$line" | grep -qiE "^(feat|add|new)"; then
        ADDED+="  - $MSG"$'\n'
    elif echo "$line" | grep -qiE "^(fix|bug|patch|hotfix|resolve)"; then
        FIXED+="  - $MSG"$'\n'
    elif echo "$line" | grep -qiE "^(remove|drop|delete|deprecate)"; then
        REMOVED+="  - $MSG"$'\n'
    elif echo "$line" | grep -qiE "^(refactor|change|update|improve|perf|style)"; then
        CHANGED+="  - $MSG"$'\n'
    else
        # Fallback: classify by keyword in message
        if echo "$line" | grep -qiE "(add|new|introduce|implement)"; then
            ADDED+="  - $MSG"$'\n'
        elif echo "$line" | grep -qiE "(fix|bug|patch|resolve|correct)"; then
            FIXED+="  - $MSG"$'\n'
        elif echo "$line" | grep -qiE "(remove|drop|delete|deprecate)"; then
            REMOVED+="  - $MSG"$'\n'
        elif echo "$line" | grep -qiE "(refactor|change|update|improve|perf|style|tweak)"; then
            CHANGED+="  - $MSG"$'\n'
        else
            OTHER+="  - $MSG"$'\n'
        fi
    fi
done <<< "$COMMITS"

# Write sections
if [ -n "$ADDED" ]; then
    echo "### Added" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$ADDED" >> "$OUTPUT"
fi

if [ -n "$FIXED" ]; then
    echo "### Fixed" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$FIXED" >> "$OUTPUT"
fi

if [ -n "$CHANGED" ]; then
    echo "### Changed" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$CHANGED" >> "$OUTPUT"
fi

if [ -n "$REMOVED" ]; then
    echo "### Removed" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$REMOVED" >> "$OUTPUT"
fi

if [ -n "$OTHER" ]; then
    echo "### Other" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "$OTHER" >> "$OUTPUT"
fi

COMMIT_COUNT=$(echo "$COMMITS" | wc -l)
echo "✅ Generated $OUTPUT with $COMMIT_COUNT commits (since: ${SINCE_TAG:-beginning})"
