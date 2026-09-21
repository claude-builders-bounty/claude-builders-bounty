#!/usr/bin/env bash
# ==============================================================================
# changelog.sh — Automated Git Changelog Generator
# Generates or updates CHANGELOG.md following the 'Keep a Changelog' standard.
# ==============================================================================

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
TARGET_TAG="${2:-}"
VERSION="${3:-Unreleased}"
DATE="$(date +%Y-%m-%d)"

# Ensure we are in a git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: current directory is not a git repository." >&2
    exit 1
fi

# Determine previous tag if not explicitly given
if [ -z "$TARGET_TAG" ]; then
    PREV_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
else
    PREV_TAG="$TARGET_TAG"
fi

if [ -n "$PREV_TAG" ]; then
    RANGE="${PREV_TAG}..HEAD"
    echo "Analyzing commits in range: ${RANGE}"
else
    RANGE="HEAD"
    echo "No git tags found. Analyzing all commits up to HEAD."
fi

# Temporary storage for classified entries
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

ADDED_FILE="${TMP_DIR}/added.txt"
FIXED_FILE="${TMP_DIR}/fixed.txt"
CHANGED_FILE="${TMP_DIR}/changed.txt"
REMOVED_FILE="${TMP_DIR}/removed.txt"
SECURITY_FILE="${TMP_DIR}/security.txt"
OTHER_FILE="${TMP_DIR}/other.txt"

touch "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE" "$SECURITY_FILE" "$OTHER_FILE"

# Extract git log: hash, author, subject
git log "$RANGE" --no-merges --pretty=tformat:"%h%x09%s" | while IFS=$'\t' read -r HASH SUBJECT; do
    [ -z "$SUBJECT" ] && continue

    CLEAN_MSG="$SUBJECT"
    # Format entry: - Subject ([hash])
    ENTRY="- ${CLEAN_MSG} (\`${HASH}\`)"

    # Categorize based on Conventional Commits or common keywords
    if echo "$SUBJECT" | grep -iE '^(feat|add|new|feature)(\(.*\))?:' >/dev/null; then
        MSG=$(echo "$CLEAN_MSG" | sed -E 's/^(feat|add|new|feature)(\(.*\))?:\s*//I')
        echo "- ${MSG} (\`${HASH}\`)" >> "$ADDED_FILE"
    elif echo "$SUBJECT" | grep -iE '^(fix|bug|patch|hotfix)(\(.*\))?:' >/dev/null; then
        MSG=$(echo "$CLEAN_MSG" | sed -E 's/^(fix|bug|patch|hotfix)(\(.*\))?:\s*//I')
        echo "- ${MSG} (\`${HASH}\`)" >> "$FIXED_FILE"
    elif echo "$SUBJECT" | grep -iE '^(remove|rm|delete|drop|deprecate)(\(.*\))?:' >/dev/null; then
        MSG=$(echo "$CLEAN_MSG" | sed -E 's/^(remove|rm|delete|drop|deprecate)(\(.*\))?:\s*//I')
        echo "- ${MSG} (\`${HASH}\`)" >> "$REMOVED_FILE"
    elif echo "$SUBJECT" | grep -iE '^(sec|security)(\(.*\))?:' >/dev/null; then
        MSG=$(echo "$CLEAN_MSG" | sed -E 's/^(sec|security)(\(.*\))?:\s*//I')
        echo "- ${MSG} (\`${HASH}\`)" >> "$SECURITY_FILE"
    elif echo "$SUBJECT" | grep -iE '^(refactor|perf|change|update|chore|style|docs)(\(.*\))?:' >/dev/null; then
        MSG=$(echo "$CLEAN_MSG" | sed -E 's/^(refactor|perf|change|update|chore|style|docs)(\(.*\))?:\s*//I')
        echo "- ${MSG} (\`${HASH}\`)" >> "$CHANGED_FILE"
    else
        echo "$ENTRY" >> "$OTHER_FILE"
    fi
done

# Build the release markdown block
RELEASE_MD="${TMP_DIR}/release.md"
{
    echo "## [${VERSION}] - ${DATE}"
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

    if [ -s "$SECURITY_FILE" ]; then
        echo "### Security"
        cat "$SECURITY_FILE"
        echo ""
    fi

    if [ -s "$OTHER_FILE" ]; then
        echo "### Other Changes"
        cat "$OTHER_FILE"
        echo ""
    fi
} > "$RELEASE_MD"

# Combine into output file
FINAL_MD="${TMP_DIR}/final.md"
if [ -f "$OUTPUT_FILE" ]; then
    # If CHANGELOG already exists, prepend below title
    if grep -q "^# Changelog" "$OUTPUT_FILE"; then
        sed '/^# Changelog/r '"$RELEASE_MD" "$OUTPUT_FILE" > "$FINAL_MD"
    else
        {
            echo "# Changelog"
            echo ""
            cat "$RELEASE_MD"
            cat "$OUTPUT_FILE"
        } > "$FINAL_MD"
    fi
else
    {
        echo "# Changelog"
        echo ""
        echo "All notable changes to this project will be documented in this file."
        echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)."
        echo ""
        cat "$RELEASE_MD"
    } > "$FINAL_MD"
fi

cp "$FINAL_MD" "$OUTPUT_FILE"
echo "Successfully generated changelog at: ${OUTPUT_FILE}"
