#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--repo PATH] [--tag FROM_TAG]
# Works via `/generate-changelog` command in Claude Code or standalone
set -euo pipefail

REPO="${2:-.}"
FROM_TAG="${4:-}"
OUTPUT="CHANGELOG.md"

cd "$REPO"

# Determine the last tag if not provided
if [ -z "$FROM_TAG" ]; then
    FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
fi

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "Generated from \`${FROM_TAG}\` to \`HEAD\`" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Categorize commits
echo "## Added" >> "$OUTPUT"
git log "$FROM_TAG..HEAD" --pretty=format:"%s" --grep="^feat" -i 2>/dev/null | sed 's/^/- /' >> "$OUTPUT" || true
git log "$FROM_TAG..HEAD" --pretty=format:"%s" --grep="^add" -i 2>/dev/null | sed 's/^/- /' >> "$OUTPUT" || true
echo "" >> "$OUTPUT"

echo "## Fixed" >> "$OUTPUT"
git log "$FROM_TAG..HEAD" --pretty=format:"%s" --grep="^fix" -i 2>/dev/null | sed 's/^/- /' >> "$OUTPUT" || true
git log "$FROM_TAG..HEAD" --pretty=format:"%s" --grep="^bug" -i 2>/dev/null | sed 's/^/- /' >> "$OUTPUT" || true
echo "" >> "$OUTPUT"

echo "## Changed" >> "$OUTPUT"
git log "$FROM_TAG..HEAD" --pretty=format:"%s" --grep="^refactor\|^update\|^chore" -i 2>/dev/null | sed 's/^/- /' >> "$OUTPUT" || true
echo "" >> "$OUTPUT"

echo "## Removed" >> "$OUTPUT"
git log "$FROM_TAG..HEAD" --pretty=format:"%s" --grep="^remove\|^rm\|^delete" -i 2>/dev/null | sed 's/^/- /' >> "$OUTPUT" || true
echo "" >> "$OUTPUT"

# If still empty, dump all commits uncategorized
if [ ! -s "$OUTPUT" ]; then
    echo "# Changelog" > "$OUTPUT"
    echo "" >> "$OUTPUT"
    git log "$FROM_TAG..HEAD" --pretty=format:"- %s (%an)" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

echo "✅ CHANGELOG.md generated ($(wc -l < "$OUTPUT") lines)"
