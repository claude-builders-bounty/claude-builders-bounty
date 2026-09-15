#!/usr/bin/env bash
# scripts/changelog.sh — Generate structured CHANGELOG from git history

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
DATE=$(date +"%Y-%m-%d")

# 1. Determine commit range
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
    VERSION_TITLE="Unreleased (since ${LAST_TAG})"
else
    RANGE="HEAD"
    VERSION_TITLE="Initial Release (${DATE})"
fi

# Temp files for categories
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

touch "$TMP_DIR/added.txt" "$TMP_DIR/fixed.txt" "$TMP_DIR/changed.txt" "$TMP_DIR/removed.txt" "$TMP_DIR/other.txt"

# 2. Parse commits
if [ -n "$LAST_TAG" ]; then
    COMMITS=$(git log "${RANGE}" --pretty=format:"%s|%h|%an")
else
    COMMITS=$(git log --pretty=format:"%s|%h|%an")
fi

if [ -z "$COMMITS" ]; then
    echo "No commits found in range: ${RANGE}"
    exit 0
fi

while IFS='|' read -r subject hash author; do
    [ -z "$subject" ] && continue
    clean_subj=$(echo "$subject" | sed -E 's/^[a-zA-Z]+(\([a-zA-Z0-9_-]+\))?!?: //')
    entry="- ${clean_subj} ([${hash}](https://github.com/claude-builders-bounty/claude-builders-bounty/commit/${hash})) — @${author}"
    
    lower_subj=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lower_subj" =~ ^(feat|add|new) ]]; then
        echo "$entry" >> "$TMP_DIR/added.txt"
    elif [[ "$lower_subj" =~ ^(fix|bug|patch|resolve) ]]; then
        echo "$entry" >> "$TMP_DIR/fixed.txt"
    elif [[ "$lower_subj" =~ ^(remove|deprecate|delete|drop) ]]; then
        echo "$entry" >> "$TMP_DIR/removed.txt"
    elif [[ "$lower_subj" =~ ^(refactor|perf|style|chore|docs|update|change) ]]; then
        echo "$entry" >> "$TMP_DIR/changed.txt"
    else
        echo "$entry" >> "$TMP_DIR/changed.txt"
    fi
done <<< "$COMMITS"

# 3. Assemble CHANGELOG snippet
NEW_BLOCK=$(cat <<EOF
## [${VERSION_TITLE}] - ${DATE}

EOF
)

if [ -s "$TMP_DIR/added.txt" ]; then
    NEW_BLOCK="${NEW_BLOCK}### Added\n$(cat "$TMP_DIR/added.txt")\n\n"
fi

if [ -s "$TMP_DIR/fixed.txt" ]; then
    NEW_BLOCK="${NEW_BLOCK}### Fixed\n$(cat "$TMP_DIR/fixed.txt")\n\n"
fi

if [ -s "$TMP_DIR/changed.txt" ]; then
    NEW_BLOCK="${NEW_BLOCK}### Changed\n$(cat "$TMP_DIR/changed.txt")\n\n"
fi

if [ -s "$TMP_DIR/removed.txt" ]; then
    NEW_BLOCK="${NEW_BLOCK}### Removed\n$(cat "$TMP_DIR/removed.txt")\n\n"
fi

# Prepend or write output file
if [ -f "$OUTPUT_FILE" ]; then
    TMP_OUT=$(mktemp)
    echo -e "$NEW_BLOCK" > "$TMP_OUT"
    cat "$OUTPUT_FILE" >> "$TMP_OUT"
    mv "$TMP_OUT" "$OUTPUT_FILE"
else
    cat <<EOF > "$OUTPUT_FILE"
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

EOF
    echo -e "$NEW_BLOCK" >> "$OUTPUT_FILE"
fi

echo "Successfully updated ${OUTPUT_FILE}!"
