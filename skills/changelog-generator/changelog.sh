#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
# Categorizes commits since the last git tag into Added/Fixed/Changed/Removed

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
DATE=$(date +%Y-%m-%d)

# Ensure we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Error: not inside a git repository"
    exit 1
fi

# Find the last tag, or use root commit if no tags exist
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -n "$LAST_TAG" ]]; then
    RANGE="${LAST_TAG}..HEAD"
    VERSION_LABEL="Unreleased (since ${LAST_TAG})"
else
    RANGE="HEAD"
    VERSION_LABEL="Unreleased"
fi

# Collect commits: hash | subject
COMMITS=$(git log "$RANGE" --pretty=format:"%h | %s" 2>/dev/null || git log --pretty=format:"%h | %s")

if [[ -z "$COMMITS" ]]; then
    echo "No commits found since ${LAST_TAG:-initial commit}."
    exit 0
fi

# Category arrays
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

# Strip conventional commit prefix from a message
strip_prefix() {
    echo "$1" | sed -E 's/^(feat|fix|refactor|perf|style|docs|build|ci|chore|revert|test)(\([^)]*\))?[!]?:\s*//'
}

# Categorize each commit
while IFS= read -r line; do
    HASH=$(echo "$line" | cut -d'|' -f1 | xargs)
    MSG=$(echo "$line" | cut -d'|' -f2- | xargs)
    MSG_LOWER=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')
    CLEAN=$(strip_prefix "$MSG")

    ENTRY="- ${CLEAN} (${HASH})"

    # Match by conventional commit prefix first, then by keywords
    if [[ "$MSG_LOWER" =~ ^feat[:\(] ]]; then
        ADDED+=("$ENTRY")
    elif [[ "$MSG_LOWER" =~ ^fix[:\(] ]]; then
        FIXED+=("$ENTRY")
    elif [[ "$MSG_LOWER" =~ ^revert[:\(] ]]; then
        REMOVED+=("$ENTRY")
    elif [[ "$MSG_LOWER" =~ ^(refactor|perf|style|docs|build|ci|chore|test)[:\(] ]]; then
        CHANGED+=("$ENTRY")
    # Keyword fallback
    elif [[ "$MSG_LOWER" =~ (^|[[:space:]])(add|new|introduce|implement|create)[[:space:]ed] ]]; then
        ADDED+=("$ENTRY")
    elif [[ "$MSG_LOWER" =~ (^|[[:space:]])(fix|bug|patch|resolve|correct)[[:space:]ed] ]]; then
        FIXED+=("$ENTRY")
    elif [[ "$MSG_LOWER" =~ (^|[[:space:]])(remove|delete|deprecate|drop)[[:space:]ed] ]]; then
        REMOVED+=("$ENTRY")
    else
        CHANGED+=("$ENTRY")
    fi
done <<< "$COMMITS"

# Build the new section
NEW_SECTION="## [${VERSION_LABEL}] — ${DATE}"
NEW_SECTION+="\n"

if [[ ${#ADDED[@]} -gt 0 ]]; then
    NEW_SECTION+="\n### Added\n"
    for e in "${ADDED[@]}"; do NEW_SECTION+="${e}\n"; done
fi

if [[ ${#FIXED[@]} -gt 0 ]]; then
    NEW_SECTION+="\n### Fixed\n"
    for e in "${FIXED[@]}"; do NEW_SECTION+="${e}\n"; done
fi

if [[ ${#CHANGED[@]} -gt 0 ]]; then
    NEW_SECTION+="\n### Changed\n"
    for e in "${CHANGED[@]}"; do NEW_SECTION+="${e}\n"; done
fi

if [[ ${#REMOVED[@]} -gt 0 ]]; then
    NEW_SECTION+="\n### Removed\n"
    for e in "${REMOVED[@]}"; do NEW_SECTION+="${e}\n"; done
fi

# Write or prepend to CHANGELOG.md
if [[ -f "$OUTPUT" ]]; then
    # Preserve existing content — insert new section after the header
    EXISTING=$(cat "$OUTPUT")
    HEADER="# Changelog"
    REST="${EXISTING#*"$HEADER"}"
    echo -e "${HEADER}\n\n$(echo -e "$NEW_SECTION")\n${REST}" > "$OUTPUT"
else
    echo -e "# Changelog\n\n$(echo -e "$NEW_SECTION")" > "$OUTPUT"
fi

# Summary
TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))
echo "✅ CHANGELOG.md generated — ${TOTAL} commits categorized:"
[[ ${#ADDED[@]} -gt 0 ]]   && echo "   Added:   ${#ADDED[@]}"
[[ ${#FIXED[@]} -gt 0 ]]   && echo "   Fixed:   ${#FIXED[@]}"
[[ ${#CHANGED[@]} -gt 0 ]] && echo "   Changed: ${#CHANGED[@]}"
[[ ${#REMOVED[@]} -gt 0 ]] && echo "   Removed: ${#REMOVED[@]}"
echo "Output: ${OUTPUT}"
