#!/usr/bin/env bash
# changelog.sh - Automatically generate structured CHANGELOG.md from git history
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_DIR="${2:-.}"

cd "$REPO_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not a git repository ($REPO_DIR)" >&2
    exit 1
fi

# Find last git tag or initial commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
    COMMIT_RANGE="${LAST_TAG}..HEAD"
    VERSION_HEADER="Changes since tag: $LAST_TAG"
else
    COMMIT_RANGE="HEAD"
    VERSION_HEADER="Initial Release (all commits)"
fi

DATE_STR=$(date -u +"%Y-%m-%d")

# Temporary files for categories
TMP_ADDED=$(mktemp)
TMP_FIXED=$(mktemp)
TMP_CHANGED=$(mktemp)
TMP_REMOVED=$(mktemp)
TMP_OTHER=$(mktemp)

trap 'rm -f "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED" "$TMP_OTHER"' EXIT

# Fetch commits: hash|author|message
git log "$COMMIT_RANGE" --no-merges --pretty=format:"%h|%s" | while IFS='|' read -r hash subject; do
    [ -z "$hash" ] && continue
    clean_msg="$subject ([${hash}](commit/${hash}))"
    
    # Categorization regex based on Conventional Commits & keywords
    case "$subject" in
        feat*|Feat*|add*|Add*|*implement*|*support*)
            echo "- $clean_msg" >> "$TMP_ADDED"
            ;;
        fix*|Fix*|bug*|Bug*|patch*|Patch*|*resolve*)
            echo "- $clean_msg" >> "$TMP_FIXED"
            ;;
        change*|Change*|refactor*|Refactor*|perf*|Perf*|style*|Style*|chore*|Chore*)
            echo "- $clean_msg" >> "$TMP_CHANGED"
            ;;
        remove*|Remove*|deprecat*|Deprecat*|delete*|Delete*)
            echo "- $clean_msg" >> "$TMP_REMOVED"
            ;;
        *)
            echo "- $clean_msg" >> "$TMP_OTHER"
            ;;
    esac
done

# Assemble CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project are documented in this file."
    echo "Format conforms to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)."
    echo ""
    echo "## [Unreleased] - $DATE_STR ($VERSION_HEADER)"
    echo ""

    if [ -s "$TMP_ADDED" ]; then
        echo "### Added"
        cat "$TMP_ADDED"
        echo ""
    fi

    if [ -s "$TMP_FIXED" ]; then
        echo "### Fixed"
        cat "$TMP_FIXED"
        echo ""
    fi

    if [ -s "$TMP_CHANGED" ]; then
        echo "### Changed"
        cat "$TMP_CHANGED"
        echo ""
    fi

    if [ -s "$TMP_REMOVED" ]; then
        echo "### Removed"
        cat "$TMP_REMOVED"
        echo ""
    fi

    if [ -s "$TMP_OTHER" ]; then
        echo "### Other Changes"
        cat "$TMP_OTHER"
        echo ""
    fi
} > "$OUTPUT_FILE"

echo "Changelog written to $OUTPUT_FILE ($DATE_STR)"
