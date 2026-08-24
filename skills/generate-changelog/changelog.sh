#!/usr/bin/env bash
# generate-changelog.sh
# Generates a structured Keep-a-Changelog formatted CHANGELOG.md from git history.
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
SINCE_REF="${2:-}"

# Detect last tag if no reference provided
if [ -z "$SINCE_REF" ]; then
    if git describe --tags --abbrev=0 2>/dev/null; then
        LAST_TAG=$(git describe --tags --abbrev=0)
        COMMIT_RANGE="${LAST_TAG}..HEAD"
        VERSION_HEADER="## [Unreleased] - $(date +%Y-%m-%d)"
    else
        COMMIT_RANGE="HEAD"
        VERSION_HEADER="## [1.0.0] - $(date +%Y-%m-%d)"
    fi
else
    COMMIT_RANGE="${SINCE_REF}..HEAD"
    VERSION_HEADER="## [Unreleased] - $(date +%Y-%m-%d)"
fi

echo "Scanning commits in range: ${COMMIT_RANGE}..."

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line || [ -n "$line" ]; do
    [ -z "$line" ] && continue
    
    HASH=$(echo "$line" | awk '{print $1}')
    MSG=$(echo "$line" | cut -d' ' -f2-)
    
    # Conventional commit parsing
    if echo "$MSG" | grep -Eq '^(feat|feature)(\(.*\))?:'; then
        CLEAN_MSG=$(echo "$MSG" | sed -E 's/^(feat|feature)(\(.*\))?:\s*//')
        ADDED="${ADDED}- ${CLEAN_MSG} ([${HASH}](commit/${HASH}))"$'\n'
    elif echo "$MSG" | grep -Eq '^(fix|bugfix|patch)(\(.*\))?:'; then
        CLEAN_MSG=$(echo "$MSG" | sed -E 's/^(fix|bugfix|patch)(\(.*\))?:\s*//')
        FIXED="${FIXED}- ${CLEAN_MSG} ([${HASH}](commit/${HASH}))"$'\n'
    elif echo "$MSG" | grep -Eq '^(refactor|perf|chore|docs|style|build|ci)(\(.*\))?:'; then
        CLEAN_MSG=$(echo "$MSG" | sed -E 's/^(refactor|perf|chore|docs|style|build|ci)(\(.*\))?:\s*//')
        CHANGED="${CHANGED}- ${CLEAN_MSG} ([${HASH}](commit/${HASH}))"$'\n'
    elif echo "$MSG" | grep -Eq '^(revert|remove|deprecated)(\(.*\))?:'; then
        CLEAN_MSG=$(echo "$MSG" | sed -E 's/^(revert|remove|deprecated)(\(.*\))?:\s*//')
        REMOVED="${REMOVED}- ${CLEAN_MSG} ([${HASH}](commit/${HASH}))"$'\n'
    else
        OTHER="${OTHER}- ${MSG} ([${HASH}](commit/${HASH}))"$'\n'
    fi
done < <(git log "${COMMIT_RANGE}" --oneline --no-merges 2>/dev/null || true)

# Build formatted markdown
CHANGELOG_ENTRY=""
CHANGELOG_ENTRY="${VERSION_HEADER}"$'\n\n'

if [ -n "$ADDED" ]; then
    CHANGELOG_ENTRY="${CHANGELOG_ENTRY}### Added"$'\n'"${ADDED}"$'\n'
fi

if [ -n "$FIXED" ]; then
    CHANGELOG_ENTRY="${CHANGELOG_ENTRY}### Fixed"$'\n'"${FIXED}"$'\n'
fi

if [ -n "$CHANGED" ]; then
    CHANGELOG_ENTRY="${CHANGELOG_ENTRY}### Changed"$'\n'"${CHANGED}"$'\n'
fi

if [ -n "$REMOVED" ]; then
    CHANGELOG_ENTRY="${CHANGELOG_ENTRY}### Removed"$'\n'"${REMOVED}"$'\n'
fi

if [ -n "$OTHER" ]; then
    CHANGELOG_ENTRY="${CHANGELOG_ENTRY}### Other Changes"$'\n'"${OTHER}"$'\n'
fi

# Prepend or create CHANGELOG.md
if [ -f "$OUTPUT_FILE" ]; then
    TEMP_FILE=$(mktemp)
    echo "$CHANGELOG_ENTRY" > "$TEMP_FILE"
    echo "---" >> "$TEMP_FILE"
    cat "$OUTPUT_FILE" >> "$TEMP_FILE"
    mv "$TEMP_FILE" "$OUTPUT_FILE"
    echo "Updated ${OUTPUT_FILE} with new release notes."
else
    cat << 'EOF' > "$OUTPUT_FILE"
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

EOF
    echo "$CHANGELOG_ENTRY" >> "$OUTPUT_FILE"
    echo "Created ${OUTPUT_FILE} with initial release notes."
fi
