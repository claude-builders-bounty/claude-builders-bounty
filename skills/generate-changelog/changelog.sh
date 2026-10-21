#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Categorizes conventional commits (feat, fix, refactor/perf, chore/docs) into:
# Added, Fixed, Changed, Removed.

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_DIR="${2:-.}"

cd "$REPO_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not a git repository." >&2
    exit 1
fi

# Find the most recent tag, or start from initial commit if no tag exists
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
    VERSION_TITLE="Changes since ${LAST_TAG}"
else
    RANGE="HEAD"
    VERSION_TITLE="Unreleased"
fi

TODAY=$(date +%Y-%m-%d)

TMP_ADDED=$(mktemp)
TMP_FIXED=$(mktemp)
TMP_CHANGED=$(mktemp)
TMP_REMOVED=$(mktemp)
TMP_OTHER=$(mktemp)

cleanup() {
    rm -f "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED" "$TMP_OTHER"
}
trap cleanup EXIT

# Parse git log using tformat: to guarantee trailing newline and prevent dropped commits
git log "$RANGE" --no-merges --pretty=tformat:"%s|%h|%an" | while IFS="|" read -r msg hash author || [ -n "$msg" ]; do
    [ -z "$msg" ] && continue
    
    # Strip conventional commit prefixes and categorize
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    entry="- ${msg} (\`${hash}\` by @${author})"
    
    if [[ "$lower_msg" =~ ^(feat|add|feature)(\(.*\))?: ]]; then
        echo "$entry" >> "$TMP_ADDED"
    elif [[ "$lower_msg" =~ ^(fix|bug|patch)(\(.*\))?: ]]; then
        echo "$entry" >> "$TMP_FIXED"
    elif [[ "$lower_msg" =~ ^(refactor|perf|change|update|chore)(\(.*\))?: ]]; then
        echo "$entry" >> "$TMP_CHANGED"
    elif [[ "$lower_msg" =~ ^(remove|deprecate|delete)(\(.*\))?: ]]; then
        echo "$entry" >> "$TMP_REMOVED"
    else
        echo "$entry" >> "$TMP_OTHER"
    fi
done

# Assemble CHANGELOG snippet
NEW_SECTION=$(mktemp)

echo "## [${VERSION_TITLE}] - ${TODAY}" >> "$NEW_SECTION"
echo "" >> "$NEW_SECTION"

if [ -s "$TMP_ADDED" ]; then
    echo "### Added" >> "$NEW_SECTION"
    cat "$TMP_ADDED" >> "$NEW_SECTION"
    echo "" >> "$NEW_SECTION"
fi

if [ -s "$TMP_FIXED" ]; then
    echo "### Fixed" >> "$NEW_SECTION"
    cat "$TMP_FIXED" >> "$NEW_SECTION"
    echo "" >> "$NEW_SECTION"
fi

if [ -s "$TMP_CHANGED" ]; then
    echo "### Changed" >> "$NEW_SECTION"
    cat "$TMP_CHANGED" >> "$NEW_SECTION"
    echo "" >> "$NEW_SECTION"
fi

if [ -s "$TMP_REMOVED" ]; then
    echo "### Removed" >> "$NEW_SECTION"
    cat "$TMP_REMOVED" >> "$NEW_SECTION"
    echo "" >> "$NEW_SECTION"
fi

if [ -s "$TMP_OTHER" ]; then
    echo "### Other Changes" >> "$NEW_SECTION"
    cat "$TMP_OTHER" >> "$NEW_SECTION"
    echo "" >> "$NEW_SECTION"
fi

# Insert or create CHANGELOG.md cleanly
if [ -f "$OUTPUT_FILE" ]; then
    TEMP_COMBINED=$(mktemp)
    if grep -q "^# " "$OUTPUT_FILE"; then
        # Keep the top title and description, insert the new section right below it
        awk -v new_sec="$(cat "$NEW_SECTION")" '
            BEGIN { inserted = 0 }
            /^## / && !inserted {
                print new_sec
                print ""
                inserted = 1
            }
            { print }
            END {
                if (!inserted) {
                    print ""
                    print new_sec
                }
            }
        ' "$OUTPUT_FILE" > "$TEMP_COMBINED"
    else
        cat "$NEW_SECTION" "$OUTPUT_FILE" > "$TEMP_COMBINED"
    fi
    mv "$TEMP_COMBINED" "$OUTPUT_FILE"
else
    {
        echo "# Changelog"
        echo ""
        echo "All notable changes to this project will be documented in this file."
        echo ""
        cat "$NEW_SECTION"
    } > "$OUTPUT_FILE"
fi

rm -f "$NEW_SECTION"

echo "✅ Generated $OUTPUT_FILE successfully for $RANGE."
