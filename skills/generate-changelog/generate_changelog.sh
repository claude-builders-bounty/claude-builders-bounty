#!/bin/bash
# Auto-generate CHANGELOG.md from git history
# Usage: ./generate_changelog.sh [output_file]

OUTPUT="${1:-CHANGELOG.md}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "All notable changes to this project will be documented in this file." >> "$OUTPUT"
echo "" >> "$OUTPUT"

if [ -n "$LAST_TAG" ]; then
    echo "## [Unreleased] — Changes since $LAST_TAG" >> "$OUTPUT"
    COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%s" 2>/dev/null)
else
    echo "## [Unreleased] — All changes" >> "$OUTPUT"
    COMMITS=$(git log --pretty=format:"%s" 2>/dev/null)
fi

echo "" >> "$OUTPUT"

# Categorize commits
ADDED=$(echo "$COMMITS" | grep -iE "^(feat|add|new|implement|introduce)" || true)
FIXED=$(echo "$COMMITS" | grep -iE "^(fix|bug|repair|correct|resolve)" || true)
CHANGED=$(echo "$COMMITS" | grep -iE "^(update|change|modify|refactor|improve|enhance|perf)" || true)
REMOVED=$(echo "$COMMITS" | grep -iE "^(remove|delete|drop|deprecate)" || true)
OTHER=$(echo "$COMMITS" | grep -viE "^(feat|add|new|implement|introduce|fix|bug|repair|correct|resolve|update|change|modify|refactor|improve|enhance|perf|remove|delete|drop|deprecate)" || true)

if [ -n "$ADDED" ]; then
    echo "### Added" >> "$OUTPUT"
    echo "$ADDED" | sed 's/^/- /' >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

if [ -n "$FIXED" ]; then
    echo "### Fixed" >> "$OUTPUT"
    echo "$FIXED" | sed 's/^/- /' >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

if [ -n "$CHANGED" ]; then
    echo "### Changed" >> "$OUTPUT"
    echo "$CHANGED" | sed 's/^/- /' >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

if [ -n "$REMOVED" ]; then
    echo "### Removed" >> "$OUTPUT"
    echo "$REMOVED" | sed 's/^/- /' >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

if [ -n "$OTHER" ]; then
    echo "### Other" >> "$OUTPUT"
    echo "$OTHER" | sed 's/^/- /' >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

echo "✓ Generated $OUTPUT"
cat "$OUTPUT"
