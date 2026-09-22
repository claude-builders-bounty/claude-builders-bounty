#!/usr/bin/env bash
set -eo pipefail

OUTPUT_FILE="CHANGELOG.md"
REPO_DIR="${1:-.}"

cd "$REPO_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Directory is not a git repository."
    exit 1
fi

LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LATEST_TAG" ]; then
    REVISION_RANGE="${LATEST_TAG}..HEAD"
    VERSION_TITLE="Unreleased (since ${LATEST_TAG})"
else
    REVISION_RANGE="HEAD"
    VERSION_TITLE="Initial Release"
fi

TODAY=$(date +%Y-%m-%d)

TMP_ADDED=$(mktemp)
TMP_FIXED=$(mktemp)
TMP_CHANGED=$(mktemp)
TMP_REMOVED=$(mktemp)
TMP_OTHER=$(mktemp)

trap 'rm -f "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED" "$TMP_OTHER"' EXIT

if [ -n "$LATEST_TAG" ]; then
    COMMITS=$(git log "$REVISION_RANGE" --pretty=format:"%s (%h)" 2>/dev/null || true)
else
    COMMITS=$(git log --pretty=format:"%s (%h)" 2>/dev/null || true)
fi

if [ -z "$COMMITS" ]; then
    echo "No new commits found to generate changelog."
    exit 0
fi

while IFS= read -r line; do
    [ -z "$line" ] && continue
    lower_line=$(echo "$line" | tr '[:upper:]' '[:lower:]')

    if [[ "$lower_line" =~ ^(feat|add|feature) ]] || [[ "$lower_line" =~ (add|new|implement|support) ]]; then
        echo "- $line" >> "$TMP_ADDED"
    elif [[ "$lower_line" =~ ^(fix|bug|hotfix) ]] || [[ "$lower_line" =~ (fix|resolve|patch|prevent|repair) ]]; then
        echo "- $line" >> "$TMP_FIXED"
    elif [[ "$lower_line" =~ ^(refactor|perf|style|docs|chore|change|update) ]] || [[ "$lower_line" =~ (update|refactor|optimize|cleanup|improve) ]]; then
        echo "- $line" >> "$TMP_CHANGED"
    elif [[ "$lower_line" =~ ^(remove|deprecate|delete) ]] || [[ "$lower_line" =~ (remove|delete|drop) ]]; then
        echo "- $line" >> "$TMP_REMOVED"
    else
        echo "- $line" >> "$TMP_CHANGED"
    fi
done <<< "$COMMITS"

NEW_ENTRY="## [${VERSION_TITLE}] - ${TODAY}\n"

append_section() {
    local title="$1"
    local file="$2"
    if [ -s "$file" ]; then
        NEW_ENTRY="${NEW_ENTRY}\n### ${title}\n"
        while IFS= read -r item; do
            NEW_ENTRY="${NEW_ENTRY}${item}\n"
        done < "$file"
    fi
}

append_section "Added" "$TMP_ADDED"
append_section "Fixed" "$TMP_FIXED"
append_section "Changed" "$TMP_CHANGED"
append_section "Removed" "$TMP_REMOVED"

HEADER="# Changelog\n\nAll notable changes to this project will be documented in this file.\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).\n\n"

if [ -f "$OUTPUT_FILE" ]; then
    EXISTING_CONTENT=$(tail -n +5 "$OUTPUT_FILE" 2>/dev/null || true)
    printf "%b%b\n%s" "$HEADER" "$NEW_ENTRY" "$EXISTING_CONTENT" > "$OUTPUT_FILE"
else
    printf "%b%b\n" "$HEADER" "$NEW_ENTRY" > "$OUTPUT_FILE"
fi

echo "Successfully updated ${OUTPUT_FILE}."
