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
VERSION_TITLE="${LATEST_TAG:-Initial Release}"
TODAY=$(date +%Y-%m-%d)

TMP_ADDED=$(mktemp); TMP_FIXED=$(mktemp); TMP_CHANGED=$(mktemp); TMP_REMOVED=$(mktemp)
trap 'rm -f "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED"' EXIT

COMMITS=$(git log --pretty=format:"%s (%h)" ${LATEST_TAG:+$LATEST_TAG..HEAD} 2>/dev/null || true)
[ -z "$COMMITS" ] && { echo "No new commits."; exit 0; }

while IFS= read -r line; do
    lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    [[ "$lower" =~ ^(feat|add|feature) ]] && echo "- $line" >> "$TMP_ADDED" ||
    [[ "$lower" =~ ^(fix|bug|hotfix) ]] && echo "- $line" >> "$TMP_FIXED" ||
    [[ "$lower" =~ ^(remove|delete) ]] && echo "- $line" >> "$TMP_REMOVED" ||
    echo "- $line" >> "$TMP_CHANGED"
done <<< "$COMMITS"

NEW_CONTENT="## [$VERSION_TITLE] - $TODAY"
[ -s "$TMP_ADDED" ] && NEW_CONTENT+=$'\n\n### Added\n'$(cat "$TMP_ADDED")
[ -s "$TMP_FIXED" ] && NEW_CONTENT+=$'\n\n### Fixed\n'$(cat "$TMP_FIXED")
[ -s "$TMP_CHANGED" ] && NEW_CONTENT+=$'\n\n### Changed\n'$(cat "$TMP_CHANGED")
[ -s "$TMP_REMOVED" ] && NEW_CONTENT+=$'\n\n### Removed\n'$(cat "$TMP_REMOVED")

HEADER="# Changelog\n\nAll notable changes to this project will be documented in this file."
if [ -f "$OUTPUT_FILE" ]; then
    printf "%s\n\n%s\n\n%s" "$HEADER" "$NEW_CONTENT" "$(cat "$OUTPUT_FILE" | sed '1,4d')" > "$OUTPUT_FILE"
else
    printf "%s\n\n%s" "$HEADER" "$NEW_CONTENT" > "$OUTPUT_FILE"
fi
echo "Successfully updated $OUTPUT_FILE."
