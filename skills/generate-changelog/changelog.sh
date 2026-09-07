#!/usr/bin/env bash
#
# Structured CHANGELOG Generator from Git History
# Categorizes commits into: Added, Fixed, Changed, Removed
#

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    COMMIT_RANGE="HEAD"
    VERSION_TITLE="Unreleased (All Commits)"
else
    COMMIT_RANGE="${LAST_TAG}..HEAD"
    VERSION_TITLE="Changes since ${LAST_TAG}"
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    hash=$(echo "$line" | cut -d' ' -f1)
    msg=$(echo "$line" | cut -d' ' -f2-)

    if echo "$msg" | grep -iE "^(feat|add|feature)(\(.*\))?:" >/dev/null; then
        clean_msg=$(echo "$msg" | sed -E 's/^(feat|add|feature)(\([^)]*\))?:\s*//I')
        ADDED="${ADDED}- ${clean_msg} ([${hash}](https://github.com/$(git config --get remote.origin.url | sed -E 's/.*github.com[:\/](.*)\.git/\1/')/commit/${hash}))\n"
    elif echo "$msg" | grep -iE "^(fix|bug|patch)(\(.*\))?:" >/dev/null; then
        clean_msg=$(echo "$msg" | sed -E 's/^(fix|bug|patch)(\([^)]*\))?:\s*//I')
        FIXED="${FIXED}- ${clean_msg} ([${hash}](https://github.com/$(git config --get remote.origin.url | sed -E 's/.*github.com[:\/](.*)\.git/\1/')/commit/${hash}))\n"
    elif echo "$msg" | grep -iE "^(refactor|perf|change|update|style)(\(.*\))?:" >/dev/null; then
        clean_msg=$(echo "$msg" | sed -E 's/^(refactor|perf|change|update|style)(\([^)]*\))?:\s*//I')
        CHANGED="${CHANGED}- ${clean_msg} ([${hash}](https://github.com/$(git config --get remote.origin.url | sed -E 's/.*github.com[:\/](.*)\.git/\1/')/commit/${hash}))\n"
    elif echo "$msg" | grep -iE "^(revert|remove|deprecate)(\(.*\))?:" >/dev/null; then
        clean_msg=$(echo "$msg" | sed -E 's/^(revert|remove|deprecate)(\([^)]*\))?:\s*//I')
        REMOVED="${REMOVED}- ${clean_msg} ([${hash}](https://github.com/$(git config --get remote.origin.url | sed -E 's/.*github.com[:\/](.*)\.git/\1/')/commit/${hash}))\n"
    else
        OTHER="${OTHER}- ${msg} ([${hash}](https://github.com/$(git config --get remote.origin.url | sed -E 's/.*github.com[:\/](.*)\.git/\1/')/commit/${hash}))\n"
    fi
done < <(git log "${COMMIT_RANGE}" --pretty=format:"%h %s")

DATE_STR=$(date +%Y-%m-%d)
HEADER="## [${VERSION_TITLE}] - ${DATE_STR}\n\n"
CONTENT=""

[ -n "$ADDED" ] && CONTENT="${CONTENT}### Added\n${ADDED}\n"
[ -n "$FIXED" ] && CONTENT="${CONTENT}### Fixed\n${FIXED}\n"
[ -n "$CHANGED" ] && CONTENT="${CONTENT}### Changed\n${CHANGED}\n"
[ -n "$REMOVED" ] && CONTENT="${CONTENT}### Removed\n${REMOVED}\n"
[ -n "$OTHER" ] && CONTENT="${CONTENT}### Other Improvements\n${OTHER}\n"

if [ -f "$OUTPUT_FILE" ]; then
    TMP_FILE=$(mktemp)
    echo -e "${HEADER}${CONTENT}" > "$TMP_FILE"
    cat "$OUTPUT_FILE" >> "$TMP_FILE"
    mv "$TMP_FILE" "$OUTPUT_FILE"
else
    echo -e "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n${HEADER}${CONTENT}" > "$OUTPUT_FILE"
fi

echo "CHANGELOG.md generated successfully!"
