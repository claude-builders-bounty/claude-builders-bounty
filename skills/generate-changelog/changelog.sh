#!/usr/bin/env bash
# Structured Git Changelog Generator - Bash Script
# Generates a categorized CHANGELOG.md adhering to Keep a Changelog.

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
VERSION="${2:-Unreleased}"

# Find previous git tag if available
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LATEST_TAG" ]; then
    RANGE="${LATEST_TAG}..HEAD"
    NOTE="Changes since \`${LATEST_TAG}\`"
else
    RANGE="HEAD"
    NOTE="Full project history"
fi

TODAY=$(date +%Y-%m-%d)

TMP_ADDED=$(mktemp)
TMP_FIXED=$(mktemp)
TMP_CHANGED=$(mktemp)
TMP_REMOVED=$(mktemp)
TMP_MAINT=$(mktemp)

trap 'rm -f "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED" "$TMP_MAINT"' EXIT

# Read git log
if [ -n "$LATEST_TAG" ]; then
    GIT_LOG=$(git log "$RANGE" --pretty=format:"%h%x09%s%x09%an")
else
    GIT_LOG=$(git log --pretty=format:"%h%x09%s%x09%an")
fi

while IFS=$'\t' read -r HASH SUBJECT AUTHOR; do
    [ -z "$HASH" ] && continue
    LINE="- ${SUBJECT} ([\`${HASH}\`]) by @${AUTHOR}"
    
    LOWER_SUB=$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$LOWER_SUB" =~ ^(feat|feature|add|create|new) ]]; then
        echo "$LINE" >> "$TMP_ADDED"
    elif [[ "$LOWER_SUB" =~ ^(fix|bugfix|hotfix|patch|resolve) ]]; then
        echo "$LINE" >> "$TMP_FIXED"
    elif [[ "$LOWER_SUB" =~ ^(remove|delete|deprecate|drop|revert) ]]; then
        echo "$LINE" >> "$TMP_REMOVED"
    elif [[ "$LOWER_SUB" =~ ^(chore|docs|test|ci|build|infra) ]]; then
        echo "$LINE" >> "$TMP_MAINT"
    else
        echo "$LINE" >> "$TMP_CHANGED"
    fi
done <<< "$GIT_LOG"

# Assemble markdown
NEW_SECTION=$(cat <<EOF
## [${VERSION}] - ${TODAY}
> ${NOTE}

EOF
)

if [ -s "$TMP_ADDED" ]; then
    NEW_SECTION+=$(printf "\n### Added\n%s\n" "$(cat "$TMP_ADDED")")
fi

if [ -s "$TMP_FIXED" ]; then
    NEW_SECTION+=$(printf "\n### Fixed\n%s\n" "$(cat "$TMP_FIXED")")
fi

if [ -s "$TMP_CHANGED" ]; then
    NEW_SECTION+=$(printf "\n### Changed\n%s\n" "$(cat "$TMP_CHANGED")")
fi

if [ -s "$TMP_REMOVED" ]; then
    NEW_SECTION+=$(printf "\n### Removed\n%s\n" "$(cat "$TMP_REMOVED")")
fi

if [ -s "$TMP_MAINT" ]; then
    NEW_SECTION+=$(printf "\n### Maintenance\n%s\n" "$(cat "$TMP_MAINT")")
fi

# Prepend or create
HEADER="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
"

if [ -f "$OUTPUT_FILE" ]; then
    EXISTING=$(tail -n +7 "$OUTPUT_FILE" 2>/dev/null || cat "$OUTPUT_FILE")
    printf "%s\n\n%s\n\n%s\n" "$HEADER" "$NEW_SECTION" "$EXISTING" > "$OUTPUT_FILE"
else
    printf "%s\n\n%s\n" "$HEADER" "$NEW_SECTION" > "$OUTPUT_FILE"
fi

echo "✅ Generated changelog in ${OUTPUT_FILE}"
