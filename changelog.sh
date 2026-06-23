#!/bin/bash
# Generate a structured CHANGELOG.md from git history
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo "# Changelog" > "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "## [Unreleased]" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    git log --pretty=format:"- %s (%h)" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "Generated: $(date +%Y-%m-%d)" >> "$OUTPUT"
    echo "Created $OUTPUT from full history"
    exit 0
fi

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## [Unreleased]" >> "$OUTPUT"
echo "" >> "$OUTPUT"

COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%s" 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
    echo "(no changes since $LAST_TAG)" >> "$OUTPUT"
    echo "No changes since $LAST_TAG"
    echo "Created $OUTPUT"
    exit 0
fi

echo "### Added" >> "$OUTPUT"
echo "" >> "$OUTPUT"
git log "$LAST_TAG"..HEAD --pretty=format:"- %s (%h)" | grep -iE "^(add|feat|create|new|implement)" | sed 's/^[a-zA-Z]*//' | sed 's/^/-/' >> "$OUTPUT" 2>/dev/null || echo "(none)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "### Fixed" >> "$OUTPUT"
echo "" >> "$OUTPUT"
git log "$LAST_TAG"..HEAD --pretty=format:"- %s (%h)" | grep -iE "^(fix|bug|patch|hotfix|correct)" | sed 's/^[a-zA-Z]*//' | sed 's/^/-/' >> "$OUTPUT" 2>/dev/null || echo "(none)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "### Changed" >> "$OUTPUT"
echo "" >> "$OUTPUT"
git log "$LAST_TAG"..HEAD --pretty=format:"- %s (%h)" | grep -iE "^(refactor|update|change|improve|migrate|bump|upgrade)" | sed 's/^[a-zA-Z]*//' | sed 's/^/-/' >> "$OUTPUT" 2>/dev/null || echo "(none)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "### Removed" >> "$OUTPUT"
echo "" >> "$OUTPUT"
git log "$LAST_TAG"..HEAD --pretty=format:"- %s (%h)" | grep -iE "^(remov|deprecat|drop|delete)" | sed 's/^[a-zA-Z]*//' | sed 's/^/-/' >> "$OUTPUT" 2>/dev/null || echo "(none)" >> "$OUTPUT"
echo "" >> "$OUTPUT"

echo "---" >> "$OUTPUT"
echo "Generated: $(date +%Y-%m-%d)" >> "$OUTPUT"

echo "Created $OUTPUT (since $LAST_TAG)"
