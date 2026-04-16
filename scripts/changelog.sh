#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
# Defaults to CHANGELOG.md in the repo root.

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

# Find the latest tag; if none exists, use all commits
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LATEST_TAG" ]; then
    RANGE="${LATEST_TAG}..HEAD"
    echo "# Changelog (since ${LATEST_TAG})" > "$OUTPUT"
else
    RANGE=""
    echo "# Changelog" > "$OUTPUT"
fi

DATE=$(date +%Y-%m-%d)
echo "" >> "$OUTPUT"
echo "_Generated on ${DATE}_" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Temporary files for categories
ADDED=$(mktemp)
FIXED=$(mktemp)
CHANGED=$(mktemp)
REMOVED=$(mktemp)
OTHER=$(mktemp)

cleanup() { rm -f "$ADDED" "$FIXED" "$CHANGED" "$REMOVED" "$OTHER"; }
trap cleanup EXIT

# Collect commits
if [ -n "$RANGE" ]; then
    GIT_LOG_CMD=(git log --oneline --no-merges "${RANGE}")
else
    GIT_LOG_CMD=(git log --oneline --no-merges)
fi

while IFS= read -r line; do
    [ -z "$line" ] && continue
    HASH="${line%% *}"
    MSG="${line#* }"

    # Strip conventional prefix for cleaner output
    CLEAN=$(echo "$MSG" | sed -E 's/^[a-z]+(\([^)]*\))?[!]?:\s*//')

    # Match conventional commit prefixes (case-insensitive)
    LOWER_MSG=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')

    if [[ "$LOWER_MSG" =~ ^feat ]]; then
        echo "- ${CLEAN} (\`${HASH}\`)" >> "$ADDED"
    elif [[ "$LOWER_MSG" =~ ^fix ]]; then
        echo "- ${CLEAN} (\`${HASH}\`)" >> "$FIXED"
    elif [[ "$LOWER_MSG" =~ ^(change|refactor) ]]; then
        echo "- ${CLEAN} (\`${HASH}\`)" >> "$CHANGED"
    elif [[ "$LOWER_MSG" =~ ^(remove|delete) ]]; then
        echo "- ${CLEAN} (\`${HASH}\`)" >> "$REMOVED"
    else
        echo "- ${MSG}" >> "$OTHER"
    fi
done < <("${GIT_LOG_CMD[@]}" 2>/dev/null)

# Write sections
write_section() {
    local title="$1"
    local file="$2"
    if [ -s "$file" ]; then
        echo "### ${title}" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
        cat "$file" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
}

write_section "Added" "$ADDED"
write_section "Fixed" "$FIXED"
write_section "Changed" "$CHANGED"
write_section "Removed" "$REMOVED"
write_section "Other" "$OTHER"

# Count
TOTAL=$(cat "$ADDED" "$FIXED" "$CHANGED" "$REMOVED" "$OTHER" 2>/dev/null | wc -l | tr -d ' ')

echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"
echo "_${TOTAL} commits since ${LATEST_TAG:-the beginning}_" >> "$OUTPUT"

echo "✅ Generated ${OUTPUT} (${TOTAL} commits)"
