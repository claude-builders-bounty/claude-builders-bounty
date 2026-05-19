#!/usr/bin/env bash
# generate-changelog.sh — structured CHANGELOG.md from git history
set -euo pipefail

SINCE_TAG="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo '')}"
OUTPUT="CHANGELOG.md"
TODAY=$(date +%Y-%m-%d)

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

if [ -n "$RANGE" ]; then
    COMMITS=$(git log "$RANGE" --pretty=format:"%s" 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%s" 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
    echo "_No commits found._" >> "$OUTPUT"
    echo "CHANGELOG.md generated (empty)"
    exit 0
fi

ADDED=""; FIXED=""; CHANGED=""; REMOVED=""; OTHER=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    MSG=$(echo "$line" | sed -E 's/^[a-z]+(\([^)]*\))?!?: //')

    if echo "$line" | grep -qiE "^(feat|add|new)"; then
        ADDED+="  - $MSG"$'\n'
    elif echo "$line" | grep -qiE "^(fix|bug|patch|hotfix|resolve)"; then
        FIXED+="  - $MSG"$'\n'
    elif echo "$line" | grep -qiE "^(remove|drop|delete|deprecate)"; then
        REMOVED+="  - $MSG"$'\n'
    elif echo "$line" | grep -qiE "^(refactor|change|update|improve|perf|style)"; then
        CHANGED+="  - $MSG"$'\n'
    else
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

[ -n "$ADDED" ] && { echo "### Added" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$ADDED" >> "$OUTPUT"; }
[ -n "$FIXED" ] && { echo "### Fixed" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$FIXED" >> "$OUTPUT"; }
[ -n "$CHANGED" ] && { echo "### Changed" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$CHANGED" >> "$OUTPUT"; }
[ -n "$REMOVED" ] && { echo "### Removed" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$REMOVED" >> "$OUTPUT"; }
[ -n "$OTHER" ] && { echo "### Other" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$OTHER" >> "$OUTPUT"; }

COMMIT_COUNT=$(echo "$COMMITS" | wc -l)
echo "Generated $OUTPUT with $COMMIT_COUNT commits (since: ${SINCE_TAG:-beginning})"
