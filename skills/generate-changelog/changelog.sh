#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Parses conventional commits (feat:, fix:, refactor:, etc.) and groups them
# into Added / Fixed / Changed / Removed sections. Supports tagged releases
# and repos with no tags at all.
#
# Usage:
#   bash changelog.sh                  # writes CHANGELOG.md in current dir
#   bash changelog.sh --output FILE    # writes to a custom path
#   bash changelog.sh --stdout         # prints to stdout instead of file
#   bash changelog.sh --from TAG       # only include commits after TAG
#   bash changelog.sh --repo DIR       # run against a different repo
#
# Compatible with bash 3.2+ (macOS default) and Linux.

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
OUTPUT_FILE="CHANGELOG.md"
USE_STDOUT=false
FROM_TAG=""
REPO_DIR="."

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
    case "$1" in
        --output)  OUTPUT_FILE="$2"; shift 2 ;;
        --stdout)  USE_STDOUT=true;  shift   ;;
        --from)    FROM_TAG="$2";    shift 2 ;;
        --repo)    REPO_DIR="$2";    shift 2 ;;
        -h|--help)
            sed -n '2,/^$/s/^# //p' "$0"
            exit 0
            ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
classify_commit() {
    local msg="$1"
    local lower
    lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

    case "$lower" in
        feat:*|feat\(*) echo "Added" ;;
        fix:*|fix\(*)   echo "Fixed" ;;
        refactor:*|refactor\(*|perf:*|perf\(*|style:*|style\(*|chore:*|chore\(*|ci:*|ci\(*|build:*|build\(*|docs:*|docs\(*)
            echo "Changed" ;;
        revert:*|revert\(*|remove:*|remove\(*|deprecate:*|deprecate\(*)
            echo "Removed" ;;
        *)
            echo "Changed" ;;
    esac
}

strip_prefix() {
    local msg="$1"
    echo "$msg" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?[!]?:[[:space:]]*//'
}

capitalize_first() {
    local str="$1"
    if [ -z "$str" ]; then
        echo ""
        return
    fi
    local first
    first=$(echo "$str" | cut -c1 | tr '[:lower:]' '[:upper:]')
    local rest
    rest=$(echo "$str" | cut -c2-)
    echo "${first}${rest}"
}

# Append a line to a named bucket (uses temp files for bash 3.2 compat)
TMPDIR_CL=$(mktemp -d)
trap 'rm -rf "$TMPDIR_CL"' EXIT

bucket_add() {
    local bucket="$1"
    local line="$2"
    echo "$line" >> "${TMPDIR_CL}/${bucket}"
}

bucket_read() {
    local bucket="$1"
    local file="${TMPDIR_CL}/${bucket}"
    if [ -f "$file" ]; then
        cat "$file"
    fi
}

bucket_has() {
    local bucket="$1"
    [ -f "${TMPDIR_CL}/${bucket}" ]
}

bucket_clear() {
    rm -f "${TMPDIR_CL}/Added" "${TMPDIR_CL}/Fixed" "${TMPDIR_CL}/Changed" "${TMPDIR_CL}/Removed"
}

# ---------------------------------------------------------------------------
# Gather tags and build revision ranges
# ---------------------------------------------------------------------------
cd "$REPO_DIR"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: $REPO_DIR is not a git repository." >&2
    exit 1
fi

# Collect version tags sorted newest first
ALL_TAGS=""
ALL_TAGS=$(git tag -l --sort=-version:refname 2>/dev/null | head -100) || true
TAG_COUNT=$(echo "$ALL_TAGS" | grep -c . 2>/dev/null || echo 0)
if [ "$ALL_TAGS" = "" ]; then
    TAG_COUNT=0
fi

# If --from is set, filter tags
if [ -n "$FROM_TAG" ] && [ "$TAG_COUNT" -gt 0 ]; then
    FILTERED=""
    while IFS= read -r t; do
        [ -z "$t" ] && continue
        if [ -z "$FILTERED" ]; then
            FILTERED="$t"
        else
            FILTERED="${FILTERED}"$'\n'"${t}"
        fi
        [ "$t" = "$FROM_TAG" ] && break
    done <<EOF
$ALL_TAGS
EOF
    ALL_TAGS="$FILTERED"
    TAG_COUNT=$(echo "$ALL_TAGS" | grep -c . 2>/dev/null || echo 0)
fi

# Build section labels and ranges in temp files
SLABELS="${TMPDIR_CL}/sec_labels"
SRANGES="${TMPDIR_CL}/sec_ranges"
: > "$SLABELS"
: > "$SRANGES"

if [ "$TAG_COUNT" -eq 0 ]; then
    echo "Unreleased" >> "$SLABELS"
    echo "HEAD" >> "$SRANGES"
else
    LATEST=$(echo "$ALL_TAGS" | head -1)
    UNRELEASED_COUNT=$(git rev-list "${LATEST}..HEAD" --count 2>/dev/null || echo 0)
    if [ "$UNRELEASED_COUNT" -gt 0 ]; then
        echo "Unreleased" >> "$SLABELS"
        echo "${LATEST}..HEAD" >> "$SRANGES"
    fi

    IDX=0
    PREV_TAG=""
    while IFS= read -r TAG; do
        [ -z "$TAG" ] && continue
        TAG_DATE=$(git log -1 --format='%as' "$TAG" 2>/dev/null || echo "")
        LABEL="$TAG"
        [ -n "$TAG_DATE" ] && LABEL="$TAG ($TAG_DATE)"

        NEXT_IDX=$((IDX + 1))
        NEXT_TAG=$(echo "$ALL_TAGS" | sed -n "${NEXT_IDX}p" 2>/dev/null || echo "")
        # Actually we need the next tag in order. Let me use a different approach.
        IDX=$((IDX + 1))
    done <<EOF
$ALL_TAGS
EOF

    # Rebuild using indexed approach
    : > "$SLABELS"
    : > "$SRANGES"

    if [ "$UNRELEASED_COUNT" -gt 0 ]; then
        echo "Unreleased" >> "$SLABELS"
        echo "${LATEST}..HEAD" >> "$SRANGES"
    fi

    TOTAL_TAGS=$TAG_COUNT
    I=1
    while [ "$I" -le "$TOTAL_TAGS" ]; do
        TAG=$(echo "$ALL_TAGS" | sed -n "${I}p")
        [ -z "$TAG" ] && break
        TAG_DATE=$(git log -1 --format='%as' "$TAG" 2>/dev/null || echo "")
        LABEL="$TAG"
        [ -n "$TAG_DATE" ] && LABEL="$TAG ($TAG_DATE)"

        NEXT_I=$((I + 1))
        if [ "$NEXT_I" -le "$TOTAL_TAGS" ]; then
            PREV_TAG=$(echo "$ALL_TAGS" | sed -n "${NEXT_I}p")
            echo "$LABEL" >> "$SLABELS"
            echo "${PREV_TAG}..${TAG}" >> "$SRANGES"
        else
            echo "$LABEL" >> "$SLABELS"
            echo "$TAG" >> "$SRANGES"
        fi
        I=$((I + 1))
    done
fi

SECTION_COUNT=$(wc -l < "$SLABELS" | tr -d ' ')

# ---------------------------------------------------------------------------
# Generate the changelog content
# ---------------------------------------------------------------------------
OUTFILE="${TMPDIR_CL}/output"
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/),"
    echo "and this project adheres to [Conventional Commits](https://www.conventionalcommits.org/)."
} > "$OUTFILE"

S=1
while [ "$S" -le "$SECTION_COUNT" ]; do
    LABEL=$(sed -n "${S}p" "$SLABELS")
    RANGE=$(sed -n "${S}p" "$SRANGES")

    # Fetch commits for this range
    COMMITS=$(git log "$RANGE" --pretty=format:"%s" --no-merges 2>/dev/null || true)

    if [ -z "$COMMITS" ]; then
        S=$((S + 1))
        continue
    fi

    # Classify each commit
    bucket_clear
    while IFS= read -r raw; do
        [ -z "$raw" ] && continue
        category=$(classify_commit "$raw")
        clean=$(strip_prefix "$raw")
        clean=$(capitalize_first "$clean")
        bucket_add "$category" "$clean"
    done <<EOF
$COMMITS
EOF

    {
        echo ""
        echo "## $LABEL"
    } >> "$OUTFILE"

    if bucket_has "Added"; then
        {
            echo ""
            echo "### Added"
            while IFS= read -r item; do
                echo "- $item"
            done < "${TMPDIR_CL}/Added"
        } >> "$OUTFILE"
    fi

    if bucket_has "Fixed"; then
        {
            echo ""
            echo "### Fixed"
            while IFS= read -r item; do
                echo "- $item"
            done < "${TMPDIR_CL}/Fixed"
        } >> "$OUTFILE"
    fi

    if bucket_has "Changed"; then
        {
            echo ""
            echo "### Changed"
            while IFS= read -r item; do
                echo "- $item"
            done < "${TMPDIR_CL}/Changed"
        } >> "$OUTFILE"
    fi

    if bucket_has "Removed"; then
        {
            echo ""
            echo "### Removed"
            while IFS= read -r item; do
                echo "- $item"
            done < "${TMPDIR_CL}/Removed"
        } >> "$OUTFILE"
    fi

    S=$((S + 1))
done

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
if $USE_STDOUT; then
    cat "$OUTFILE"
else
    cp "$OUTFILE" "$OUTPUT_FILE"
    LINE_COUNT=$(wc -l < "$OUTFILE" | tr -d ' ')
    echo "Changelog written to $OUTPUT_FILE ($LINE_COUNT lines)"
fi
