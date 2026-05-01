#!/usr/bin/env bash
#
# generate-changelog.sh — Generate CHANGELOG.md from Git History
#
# Parses conventional commits and generates a structured changelog
# categorized into: Added / Fixed / Changed / Removed
#
# Usage:
#   ./generate-changelog.sh                    # Full changelog
#   ./generate-changelog.sh --since v1.0.0     # From tag to HEAD
#   ./generate-changelog.sh --unreleased       # Since last tag only
#   ./generate-changelog.sh -o CHANGELOG.md    # Write to file
#
# Requires: git (Bash 3.2+)
#
set -euo pipefail

# ─── Argument Parsing ─────────────────────────────────────────────────────────

RANGE=""
OUTPUT_FILE=""
UNRELEASED_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --since)
            RANGE="$2..HEAD"
            shift 2
            ;;
        --unreleased)
            UNRELEASED_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS] [RANGE]"
            echo ""
            echo "Generate CHANGELOG.md from git conventional commits."
            echo ""
            echo "Options:"
            echo "  --output, -o FILE   Write output to FILE instead of stdout"
            echo "  --since TAG         Generate from TAG to HEAD"
            echo "  --unreleased        Only include commits since last tag"
            echo "  --help, -h          Show this help"
            echo ""
            echo "Categories: Added, Fixed, Changed, Removed"
            exit 0
            ;;
        *)
            RANGE="$1"
            shift
            ;;
    esac
done

# ─── Helper Functions ─────────────────────────────────────────────────────────

check_git() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo "Error: Not a git repository" >&2
        exit 1
    fi
}

get_latest_tag() {
    git describe --tags --abbrev=0 2>/dev/null || echo ""
}

# Map conventional commit type to changelog category
classify_commit() {
    local type="$1"
    case "$type" in
        feat)     echo "Added" ;;
        fix)      echo "Fixed" ;;
        remove)   echo "Removed" ;;
        *)        echo "Changed" ;;
    esac
}

# Parse conventional commit subject
# Sets: PARSE_TYPE, PARSE_SCOPE, PARSE_DESC
parse_subject() {
    local subject="$1"
    PARSE_TYPE=""
    PARSE_SCOPE=""
    PARSE_DESC="$subject"

    # Try to match type(scope): description or type!: description
    local remaining="$subject"

    # Extract type (word before first : or ()
    local type_part="${remaining%%:*}"
    # Remove everything after ( if present
    PARSE_TYPE="${type_part%%(*}"
    # Remove trailing ! if present
    PARSE_TYPE="${PARSE_TYPE%%!}"

    # Extract scope if present
    if [[ "$remaining" == *"("*")"* ]]; then
        PARSE_SCOPE="${remaining#*(}"
        PARSE_SCOPE="${PARSE_SCOPE%%)*}"
    fi

    # Extract description (after ": ")
    if [[ "$remaining" == *": "* ]]; then
        PARSE_DESC="${remaining#*: }"
    fi
}

# ─── Main Logic ───────────────────────────────────────────────────────────────

check_git

# Determine range
if [[ -z "$RANGE" && "$UNRELEASED_ONLY" == true ]]; then
    LATEST_TAG=$(get_latest_tag)
    if [[ -n "$LATEST_TAG" ]]; then
        RANGE="${LATEST_TAG}..HEAD"
    fi
fi

# Get commits
if [[ -n "$RANGE" ]]; then
    GIT_LOG=$(git log "$RANGE" --pretty=format:"%H|%s" --no-merges 2>/dev/null || true)
else
    GIT_LOG=$(git log --pretty=format:"%H|%s" --no-merges 2>/dev/null || true)
fi

if [[ -z "$GIT_LOG" ]]; then
    echo "No commits found." >&2
    exit 0
fi

# Collect entries by category (using temp files for Bash 3 compatibility)
ADDED_FILE=$(mktemp)
FIXED_FILE=$(mktemp)
CHANGED_FILE=$(mktemp)
REMOVED_FILE=$(mktemp)
trap "rm -f $ADDED_FILE $FIXED_FILE $CHANGED_FILE $REMOVED_FILE" EXIT

while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    HASH=$(echo "$line" | cut -d'|' -f1)
    SUBJECT=$(echo "$line" | cut -d'|' -f2-)
    SHORT="${HASH:0:7}"

    # Skip merge commits
    case "$SUBJECT" in
        "Merge "*) continue ;;
    esac

    # Parse conventional commit
    parse_subject "$SUBJECT"
    TYPE="$PARSE_TYPE"
    SCOPE="$PARSE_SCOPE"
    DESC="$PARSE_DESC"

    # Format entry
    if [[ -n "$SCOPE" ]]; then
        ENTRY="- **${SCOPE}:** ${DESC} (\`${SHORT}\`)"
    else
        ENTRY="- ${DESC} (\`${SHORT}\`)"
    fi

    # Classify and write to appropriate file
    TYPE_LOWER=$(echo "$TYPE" | tr '[:upper:]' '[:lower:]')
    CATEGORY=$(classify_commit "$TYPE_LOWER")

    case "$CATEGORY" in
        Added)   echo "$ENTRY" >> "$ADDED_FILE" ;;
        Fixed)   echo "$ENTRY" >> "$FIXED_FILE" ;;
        Removed) echo "$ENTRY" >> "$REMOVED_FILE" ;;
        Changed) echo "$ENTRY" >> "$CHANGED_FILE" ;;
    esac

done <<< "$GIT_LOG"

# ─── Generate Output ──────────────────────────────────────────────────────────

DATE=$(date +%Y-%m-%d)
OUTPUT=""

OUTPUT+="# Changelog"$'\n'
OUTPUT+=""$'\n'
OUTPUT+="All notable changes to this project will be documented in this file."$'\n'
OUTPUT+=""$'\n'
OUTPUT+="## [Unreleased] - ${DATE}"$'\n'
OUTPUT+=""$'\n'

# Add each category that has entries
for PAIR in "Added:${ADDED_FILE}" "Fixed:${FIXED_FILE}" "Changed:${CHANGED_FILE}" "Removed:${REMOVED_FILE}"; do
    CATEGORY="${PAIR%%:*}"
    FILE="${PAIR#*:}"
    if [[ -s "$FILE" ]]; then
        OUTPUT+="### ${CATEGORY}"$'\n'
        OUTPUT+=""$'\n'
        while IFS= read -r entry; do
            OUTPUT+="${entry}"$'\n'
        done < "$FILE"
        OUTPUT+=""$'\n'
    fi
done

# Historical releases from tags (if not unreleased-only)
if [[ "$UNRELEASED_ONLY" != true ]]; then
    PREV_TAG=""
    while IFS= read -r TAG; do
        [[ -z "$TAG" ]] && continue
        TAG_DATE=$(git log -1 --format="%ai" "$TAG" 2>/dev/null | cut -d' ' -f1)
        OUTPUT+="## [${TAG}] - ${TAG_DATE}"$'\n'
        OUTPUT+=""$'\n'
        if [[ -n "$PREV_TAG" ]]; then
            OUTPUT+="See [git log](compare/${PREV_TAG}...${TAG}) for changes."$'\n'
        else
            OUTPUT+="See [git log](compare/${TAG}...HEAD) for changes."$'\n'
        fi
        OUTPUT+=""$'\n'
        PREV_TAG="$TAG"
    done <<< "$(git tag --sort=-v:refname 2>/dev/null || true)"
fi

# Output
if [[ -n "$OUTPUT_FILE" ]]; then
    echo "$OUTPUT" > "$OUTPUT_FILE"
    echo "✅ Changelog written to ${OUTPUT_FILE}" >&2
else
    echo "$OUTPUT"
fi
