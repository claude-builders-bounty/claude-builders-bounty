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

format_subject() {
    local subj="$1"
    local hash="$2"
    local clean
    clean=$(printf '%s\n' "$subj" | sed -E 's/^[^:]*:[[:space:]]*//')
    if [ -n "$clean" ]; then
        local first rest
        first=$(printf '%s' "${clean:0:1}" | tr '[:lower:]' '[:upper:]')
        rest="${clean:1}"
        clean="${first}${rest}"
    else
        clean="$subj"
    fi
    printf -- "- %s (\`%s\`)\n" "$clean" "$hash"
}

while IFS='|' read -r HASH SUBJECT || [ -n "$HASH" ]; do
    SUBJECT="${SUBJECT%$'\r'}"
    HASH="${HASH%$'\r'}"
    [ -z "$HASH" ] && continue
    TOTAL_COMMITS=$((TOTAL_COMMITS + 1))

    if printf '%s\n' "$SUBJECT" | grep -Eqi '^(feat|add|new)(\(.*\))?!?:'; then
        format_subject "$SUBJECT" "$HASH" >> "$ADDED_FILE"
    elif printf '%s\n' "$SUBJECT" | grep -Eqi '^(fix|bug|patch)(\(.*\))?!?:'; then
        format_subject "$SUBJECT" "$HASH" >> "$FIXED_FILE"
    elif printf '%s\n' "$SUBJECT" | grep -Eqi '^(refactor|perf|style|chore|build|ci)(\(.*\))?!?:'; then
        format_subject "$SUBJECT" "$HASH" >> "$CHANGED_FILE"
    elif printf '%s\n' "$SUBJECT" | grep -Eqi '^(remove|deprecate|revert)(\(.*\))?!?:'; then
        format_subject "$SUBJECT" "$HASH" >> "$REMOVED_FILE"
    else
        printf -- "- %s (\`%s\`)\n" "$SUBJECT" "$HASH" >> "$OTHER_FILE"
    fi
done < <(git log "$RANGE" --no-merges --pretty=tformat:"%h|%s" 2>/dev/null || true)

if [ "$TOTAL_COMMITS" -eq 0 ]; then
    echo "No commits found in range ${RANGE}."
    exit 0
fi

ENTRY_FILE="$TMP_DIR/entry.md"
cat << EOF > "$ENTRY_FILE"
## [${TITLE_TAG}] - ${TODAY}

EOF

append_section() {
    local heading="$1"
    local file="$2"
    if [ -s "$file" ]; then
        echo "### ${heading}" >> "$ENTRY_FILE"
        cat "$file" >> "$ENTRY_FILE"
        echo "" >> "$ENTRY_FILE"
    fi
}

append_section "Added" "$ADDED_FILE"
append_section "Fixed" "$FIXED_FILE"
append_section "Changed" "$CHANGED_FILE"
append_section "Removed" "$REMOVED_FILE"
append_section "Other Changes" "$OTHER_FILE"

# Prepend or create CHANGELOG.md
if [ -f "$CHANGELOG_FILE" ]; then
    if grep -q "^# Changelog" "$CHANGELOG_FILE"; then
        awk -v entry="$ENTRY_FILE" '
            !inserted && /^# Changelog/ {
                print
                print ""
                while ((getline line < entry) > 0) print line
                close(entry)
                inserted = 1
                next
            }
            { print }
        ' "$CHANGELOG_FILE" > "$TMP_DIR/new_changelog.md"
        mv "$TMP_DIR/new_changelog.md" "$CHANGELOG_FILE"
    else
        cat "$ENTRY_FILE" "$CHANGELOG_FILE" > "$TMP_DIR/new_changelog.md"
        mv "$TMP_DIR/new_changelog.md" "$CHANGELOG_FILE"
    fi
else
    {
        echo "# Changelog"
        echo ""
        echo "All notable changes to this project will be documented in this file."
        echo ""
        cat "$ENTRY_FILE"
    } > "$CHANGELOG_FILE"
fi

echo "Successfully updated ${CHANGELOG_FILE} (${TOTAL_COMMITS} commits processed)."
