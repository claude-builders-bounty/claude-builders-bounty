#!/usr/bin/env bash
#
# changelog.sh — Generate structured CHANGELOG.md from git history
# Conforms to Keep a Changelog standard (Added, Fixed, Changed, Removed).
#

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
DATE_STR="$(date +%Y-%m-%d)"

# 1. Determine baseline tag or commit range
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    LAST_TAG="$(git describe --tags --abbrev=0)"
    COMMIT_RANGE="${LAST_TAG}..HEAD"
    RELEASE_TITLE="## [Unreleased] - ${DATE_STR} (since ${LAST_TAG})"
else
    LAST_TAG=""
    COMMIT_RANGE="HEAD"
    RELEASE_TITLE="## [Unreleased] - ${DATE_STR}"
fi

# Temp files for categories
TMP_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t 'changelog')"
trap 'rm -rf "${TMP_DIR}"' EXIT

ADDED_FILE="${TMP_DIR}/added.txt"
FIXED_FILE="${TMP_DIR}/fixed.txt"
CHANGED_FILE="${TMP_DIR}/changed.txt"
REMOVED_FILE="${TMP_DIR}/removed.txt"
OTHER_FILE="${TMP_DIR}/other.txt"

touch "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE" "$OTHER_FILE"

# 2. Extract and categorize commits
git log ${COMMIT_RANGE} --pretty=format:"%s|%h|%an" | while IFS="|" read -r msg hash author; do
    [ -z "$msg" ] && continue
    clean_msg="$(echo "$msg" | sed -E 's/^(feat|feature|add|fix|bug|patch|refactor|perf|chore|docs|style|revert|remove|drop)(\([^)]+\))?!?:? //I')"
    entry="- ${clean_msg} (\`${hash}\` by ${author})"

    case "$msg" in
        [Ff][Ee][Aa][Tt]*|[Aa][Dd][Dd]*|[Nn][Ee][Ww]*)
            echo "$entry" >> "$ADDED_FILE"
            ;;
        [Ff][Ii][Xx]*|[Bb][Uu][Gg]*|[Pp][Aa][Tt][Cc][Hh]*|[Hh][Oo][Tt][Ff][Ii][Xx]*)
            echo "$entry" >> "$FIXED_FILE"
            ;;
        [Rr][Ee][Vv][Ee][Rr][Tt]*|[Rr][Ee][Mm][Oo][Vv][Ee]*|[Dd][Ee][Pp][Rr][Ee][Cc][Aa][Tt][Ee]*|[Dd][Rr][Oo][Pp]*)
            echo "$entry" >> "$REMOVED_FILE"
            ;;
        [Rr][Ee][Ff][Aa][Cc][Tt][Oo][Rr]*|[Pp][Ee][Rr][Ff]*|[Cc][Hh][Oo][Rr][Ee]*|[Dd][Oo][Cc][Ss]*|[Ss][Tt][Yy][Ll][Ee]*|[Uu][Pp][Dd][Aa][Tt][Ee]*)
            echo "$entry" >> "$CHANGED_FILE"
            ;;
        *)
            echo "$entry" >> "$CHANGED_FILE"
            ;;
    esac
done

# 3. Assemble new release section
NEW_SECTION="${TMP_DIR}/new_section.md"
{
    echo "$RELEASE_TITLE"
    echo ""
    if [ -s "$ADDED_FILE" ]; then
        echo "### Added"
        cat "$ADDED_FILE"
        echo ""
    fi
    if [ -s "$FIXED_FILE" ]; then
        echo "### Fixed"
        cat "$FIXED_FILE"
        echo ""
    fi
    if [ -s "$CHANGED_FILE" ]; then
        echo "### Changed"
        cat "$CHANGED_FILE"
        echo ""
    fi
    if [ -s "$REMOVED_FILE" ]; then
        echo "### Removed"
        cat "$REMOVED_FILE"
        echo ""
    fi
} > "$NEW_SECTION"

# 4. Write or prepend to CHANGELOG.md
if [ -f "$OUTPUT_FILE" ]; then
    # Keep header if present, otherwise prepend
    TMP_OUT="${TMP_DIR}/final_changelog.md"
    if grep -q "# Changelog" "$OUTPUT_FILE"; then
        sed '/# Changelog/q' "$OUTPUT_FILE" > "$TMP_OUT"
        echo "" >> "$TMP_OUT"
        cat "$NEW_SECTION" >> "$TMP_OUT"
        sed '1,/# Changelog/d' "$OUTPUT_FILE" >> "$TMP_OUT"
    else
        cat "$NEW_SECTION" > "$TMP_OUT"
        echo "" >> "$TMP_OUT"
        cat "$OUTPUT_FILE" >> "$TMP_OUT"
    fi
    mv "$TMP_OUT" "$OUTPUT_FILE"
else
    {
        echo "# Changelog"
        echo ""
        echo "All notable changes to this project will be documented in this file."
        echo "The format is based on [Keep a Changelog](https://keepachangelog.com/)."
        echo ""
        cat "$NEW_SECTION"
    } > "$OUTPUT_FILE"
fi

echo "Successfully updated ${OUTPUT_FILE}."
