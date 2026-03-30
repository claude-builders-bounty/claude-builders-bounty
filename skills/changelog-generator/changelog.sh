#!/usr/bin/env bash
# Structured CHANGELOG generator from git history
# Usage: bash changelog.sh [output_file]

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

# Check if we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Error: Not inside a git repository." >&2
    exit 1
fi

# Get the last tag, or use the first commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -z "$LAST_TAG" ]]; then
    SINCE_REF=$(git rev-list --max-parents=0 HEAD 2>/dev/null | head -1)
    TAG_LABEL="the beginning"
else
    SINCE_REF="$LAST_TAG"
    TAG_LABEL="$LAST_TAG"
fi

CURRENT_DATE=$(date +%Y-%m-%d)

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    
    HASH=$(echo "$line" | awk '{print $1}')
    MSG=$(echo "$line" | cut -d' ' -f2-)
    
    # Clean conventional commit prefix
    CLEAN_MSG=$(echo "$MSG" | sed -E 's/^(feat|fix|chore|docs|style|refactor|perf|test|ci|build)(\(.+\))?:\s*//')
    
    MSG_LOWER=$(echo "$CLEAN_MSG" | tr '[:upper:]' '[:lower:]')
    ENTRY="- ${CLEAN_MSG} (\`${HASH}\`)"
    
    if echo "$MSG_LOWER" | grep -qE '(^feat|add[^r]|new |create|implement|introduce|support )'; then
        ADDED="${ADDED}${ENTRY}\n"
    elif echo "$MSG_LOWER" | grep -qE '(^fix|bug|patch|resolve|repair|correct|hotfix)'; then
        FIXED="${FIXED}${ENTRY}\n"
    elif echo "$MSG_LOWER" | grep -qE '(remove|delete|drop |deprecat)'; then
        REMOVED="${REMOVED}${ENTRY}\n"
    else
        CHANGED="${CHANGED}${ENTRY}\n"
    fi
done < <({ git log "${SINCE_REF}..HEAD" --pretty=format:"%h %s" 2>/dev/null || git log --pretty=format:"%h %s" 2>/dev/null; echo; })

# Generate CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "## [Unreleased] — $CURRENT_DATE"
    echo ""
    echo "> Changes since ${TAG_LABEL}"
    echo ""
    
    if [[ -n "$ADDED" ]]; then
        echo "### Added"
        echo -e "$ADDED"
    fi
    
    if [[ -n "$FIXED" ]]; then
        echo "### Fixed"
        echo -e "$FIXED"
    fi
    
    if [[ -n "$CHANGED" ]]; then
        echo "### Changed"
        echo -e "$CHANGED"
    fi
    
    if [[ -n "$REMOVED" ]]; then
        echo "### Removed"
        echo -e "$REMOVED"
    fi
} > "$OUTPUT_FILE"

echo "✅ Changelog generated: $OUTPUT_FILE"
echo ""
cat "$OUTPUT_FILE"
