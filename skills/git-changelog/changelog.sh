#!/usr/bin/env bash
# Generates a structured CHANGELOG.md from git history since the latest tag

set -e

# Find the latest tag, or fallback to the root commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    RANGE="HEAD"
    TAG_LABEL="Unreleased"
else
    RANGE="${LAST_TAG}..HEAD"
    TAG_LABEL="${LAST_TAG} → HEAD"
fi

OUTPUT_FILE="${1:-CHANGELOG.md}"

TMP_ADDED=$(mktemp)
TMP_FIXED=$(mktemp)
TMP_CHANGED=$(mktemp)
TMP_REMOVED=$(mktemp)
TMP_OTHER=$(mktemp)

trap 'rm -f "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED" "$TMP_OTHER"' EXIT

# Read commits in range
git log "$RANGE" --pretty=format:"%h|%s" 2>/dev/null | while IFS="|" read -r hash msg || [ -n "$hash" ]; do
    [ -z "$msg" ] && continue
    lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

    if [[ "$lower" =~ ^(feat|add|feature)(\(.*\))?: ]]; then
        echo "- ${msg} (\`${hash}\`)" >> "$TMP_ADDED"
    elif [[ "$lower" =~ ^(fix|bug|patch)(\(.*\))?: ]]; then
        echo "- ${msg} (\`${hash}\`)" >> "$TMP_FIXED"
    elif [[ "$lower" =~ ^(change|refactor|perf|style|update)(\(.*\))?: ]]; then
        echo "- ${msg} (\`${hash}\`)" >> "$TMP_CHANGED"
    elif [[ "$lower" =~ ^(remove|deprecate|delete)(\(.*\))?: ]]; then
        echo "- ${msg} (\`${hash}\`)" >> "$TMP_REMOVED"
    else
        echo "- ${msg} (\`${hash}\`)" >> "$TMP_OTHER"
    fi
done

DATE=$(date +"%Y-%m-%d")

cat <<EOF > "$OUTPUT_FILE"
# Changelog

All notable changes to this project will be documented in this file.

## [${TAG_LABEL}] - ${DATE}

EOF

if [ -s "$TMP_ADDED" ]; then
    echo "### Added" >> "$OUTPUT_FILE"
    cat "$TMP_ADDED" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

if [ -s "$TMP_FIXED" ]; then
    echo "### Fixed" >> "$OUTPUT_FILE"
    cat "$TMP_FIXED" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

if [ -s "$TMP_CHANGED" ]; then
    echo "### Changed" >> "$OUTPUT_FILE"
    cat "$TMP_CHANGED" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

if [ -s "$TMP_REMOVED" ]; then
    echo "### Removed" >> "$OUTPUT_FILE"
    cat "$TMP_REMOVED" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

if [ -s "$TMP_OTHER" ]; then
    echo "### Other Changes" >> "$OUTPUT_FILE"
    cat "$TMP_OTHER" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

echo "✅ Generated $OUTPUT_FILE successfully."
