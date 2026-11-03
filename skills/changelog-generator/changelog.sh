#!/usr/bin/env bash
# Structured Git Changelog Generator (Bash)
# Solves Bounty #1 ($50) in claude-builders-bounty

set -euo pipefail

# Find last git tag or fallback to initial commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
    TITLE_TAG="$LAST_TAG"
else
    RANGE="HEAD"
    TITLE_TAG="Unreleased"
fi

TODAY=$(date +%Y-%m-%d)
CHANGELOG_FILE="CHANGELOG.md"

# Arrays/temporary storage for categories
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

ADDED_FILE="$TMP_DIR/added.txt"
FIXED_FILE="$TMP_DIR/fixed.txt"
CHANGED_FILE="$TMP_DIR/changed.txt"
REMOVED_FILE="$TMP_DIR/removed.txt"
OTHER_FILE="$TMP_DIR/other.txt"

touch "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE" "$OTHER_FILE"

TOTAL_COMMITS=0

while IFS='|' read -r HASH SUBJECT; do
    [ -z "$HASH" ] && continue
    TOTAL_COMMITS=$((TOTAL_COMMITS + 1))

    # Strip prefixes and categorize
    if echo "$SUBJECT" | grep -Ei '^(feat|add|new)(\(.*\))?!?:' >/dev/null; then
        CLEAN=$(echo "$SUBJECT" | sed -E 's/^(feat|add|new)(\(.*\))?!?:[[:space:]]*//I')
        CLEAN="$(echo "${CLEAN:0:1}" | tr '[:lower:]' '[:upper:]')${CLEAN:1}"
        echo "- ${CLEAN} (\`${HASH}\`)" >> "$ADDED_FILE"
    elif echo "$SUBJECT" | grep -Ei '^(fix|bug|patch)(\(.*\))?!?:' >/dev/null; then
        CLEAN=$(echo "$SUBJECT" | sed -E 's/^(fix|bug|patch)(\(.*\))?!?:[[:space:]]*//I')
        CLEAN="$(echo "${CLEAN:0:1}" | tr '[:lower:]' '[:upper:]')${CLEAN:1}"
        echo "- ${CLEAN} (\`${HASH}\`)" >> "$FIXED_FILE"
    elif echo "$SUBJECT" | grep -Ei '^(refactor|perf|style|chore|build|ci)(\(.*\))?!?:' >/dev/null; then
        CLEAN=$(echo "$SUBJECT" | sed -E 's/^(refactor|perf|style|chore|build|ci)(\(.*\))?!?:[[:space:]]*//I')
        CLEAN="$(echo "${CLEAN:0:1}" | tr '[:lower:]' '[:upper:]')${CLEAN:1}"
        echo "- ${CLEAN} (\`${HASH}\`)" >> "$CHANGED_FILE"
    elif echo "$SUBJECT" | grep -Ei '^(remove|deprecate|revert)(\(.*\))?!?:' >/dev/null; then
        CLEAN=$(echo "$SUBJECT" | sed -E 's/^(remove|deprecate|revert)(\(.*\))?!?:[[:space:]]*//I')
        CLEAN="$(echo "${CLEAN:0:1}" | tr '[:lower:]' '[:upper:]')${CLEAN:1}"
        echo "- ${CLEAN} (\`${HASH}\`)" >> "$REMOVED_FILE"
    else
        echo "- ${SUBJECT} (\`${HASH}\`)" >> "$OTHER_FILE"
    fi
done < <(git log "$RANGE" --no-merges --pretty=format:"%h|%s" 2>/dev/null || true)

if [ "$TOTAL_COMMITS" -eq 0 ]; then
    echo "No commits found in range ${RANGE}."
    exit 0
fi

ENTRY_FILE="$TMP_DIR/entry.md"
cat << EOF > "$ENTRY_FILE"
## [${TITLE_TAG}] - ${TODAY}

EOF

if [ -s "$ADDED_FILE" ]; then
    echo "### Added" >> "$ENTRY_FILE"
    cat "$ADDED_FILE" >> "$ENTRY_FILE"
    echo "" >> "$ENTRY_FILE"
fi

if [ -s "$FIXED_FILE" ]; then
    echo "### Fixed" >> "$ENTRY_FILE"
    cat "$FIXED_FILE" >> "$ENTRY_FILE"
    echo "" >> "$ENTRY_FILE"
fi

if [ -s "$CHANGED_FILE" ]; then
    echo "### Changed" >> "$ENTRY_FILE"
    cat "$CHANGED_FILE" >> "$ENTRY_FILE"
    echo "" >> "$ENTRY_FILE"
fi

if [ -s "$REMOVED_FILE" ]; then
    echo "### Removed" >> "$ENTRY_FILE"
    cat "$REMOVED_FILE" >> "$ENTRY_FILE"
    echo "" >> "$ENTRY_FILE"
fi

if [ -s "$OTHER_FILE" ]; then
    echo "### Other Changes" >> "$ENTRY_FILE"
    cat "$OTHER_FILE" >> "$ENTRY_FILE"
    echo "" >> "$ENTRY_FILE"
fi

# Prepend or create CHANGELOG.md
if [ -f "$CHANGELOG_FILE" ]; then
    if grep -q "# Changelog" "$CHANGELOG_FILE"; then
        awk -v r="$(cat "$ENTRY_FILE")" '/# Changelog/{print; print ""; print r; next}1' "$CHANGELOG_FILE" > "$TMP_DIR/new_changelog.md"
        mv "$TMP_DIR/new_changelog.md" "$CHANGELOG_FILE"
    else
        cat "$ENTRY_FILE" "$CHANGELOG_FILE" > "$TMP_DIR/new_changelog.md"
        mv "$TMP_DIR/new_changelog.md" "$CHANGELOG_FILE"
    fi
else
    cat << EOF > "$CHANGELOG_FILE"
# Changelog

All notable changes to this project will be documented in this file.

$(cat "$ENTRY_FILE")
EOF
fi

echo "✅ Successfully updated ${CHANGELOG_FILE} (${TOTAL_COMMITS} commits processed)."
