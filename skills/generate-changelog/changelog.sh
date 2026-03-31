#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output-file]
#
# Reads commits since the last git tag (or all commits if no tag exists),
# categorizes them by conventional commit prefixes, and writes a formatted
# CHANGELOG.md following the Keep a Changelog standard.

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
TODAY=$(date +%Y-%m-%d)

# --- Find the last tag ---
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
    VERSION="Unreleased"
    RANGE="${LAST_TAG}..HEAD"
    echo "Found last tag: $LAST_TAG"
else
    VERSION="0.1.0"
    RANGE=""
    echo "No tags found — using full commit history"
fi

# --- Fetch commits ---
if [ -n "$RANGE" ]; then
    COMMITS=$(git log "$RANGE" --pretty=format:"%s|%h|%ad" --date=short 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%s|%h|%ad" --date=short 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
    echo "No commits found. Nothing to generate."
    exit 0
fi

# --- Categorize commits ---
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

count_added=0
count_fixed=0
count_changed=0
count_removed=0
count_other=0
count_total=0

while IFS= read -r line; do
    [ -z "$line" ] && continue

    subject=$(echo "$line" | cut -d'|' -f1)
    hash=$(echo "$line" | cut -d'|' -f2)

    # Extract the prefix (text before first colon or space)
    prefix=$(echo "$subject" | sed -E 's/^([a-zA-Z]+)[\(: ].*/\1/' | tr '[:upper:]' '[:lower:]')

    # Clean the subject: remove conventional commit prefix
    clean=$(echo "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?[: ]*//')
    # Capitalize first letter
    clean="$(echo "${clean:0:1}" | tr '[:lower:]' '[:upper:]')${clean:1}"

    entry="- ${clean} (${hash})"
    count_total=$((count_total + 1))

    case "$prefix" in
        feat|add|new|introduce|implement)
            ADDED="${ADDED}${entry}\n"
            count_added=$((count_added + 1))
            ;;
        fix|bugfix|patch|resolve|correct)
            FIXED="${FIXED}${entry}\n"
            count_fixed=$((count_fixed + 1))
            ;;
        refactor|change|update|improve|enhance|style|perf|ci|build|docs|test|chore)
            CHANGED="${CHANGED}${entry}\n"
            count_changed=$((count_changed + 1))
            ;;
        remove|delete|drop|deprecate|revert)
            REMOVED="${REMOVED}${entry}\n"
            count_removed=$((count_removed + 1))
            ;;
        *)
            OTHER="${OTHER}${entry}\n"
            count_other=$((count_other + 1))
            ;;
    esac
done <<< "$COMMITS"

# --- Write CHANGELOG.md ---
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
    echo ""
    echo "## [${VERSION}] - ${TODAY}"

    if [ -n "$ADDED" ]; then
        echo ""
        echo "### Added"
        echo -e "$ADDED" | sed '/^$/d'
    fi

    if [ -n "$FIXED" ]; then
        echo ""
        echo "### Fixed"
        echo -e "$FIXED" | sed '/^$/d'
    fi

    if [ -n "$CHANGED" ]; then
        echo ""
        echo "### Changed"
        echo -e "$CHANGED" | sed '/^$/d'
    fi

    if [ -n "$REMOVED" ]; then
        echo ""
        echo "### Removed"
        echo -e "$REMOVED" | sed '/^$/d'
    fi

    if [ -n "$OTHER" ]; then
        echo ""
        echo "### Other"
        echo -e "$OTHER" | sed '/^$/d'
    fi

    echo ""
} > "$OUTPUT"

# --- Report ---
echo ""
echo "=== Changelog Generated ==="
echo "Output:   $OUTPUT"
echo "Commits:  $count_total total"
echo "  Added:   $count_added"
echo "  Fixed:   $count_fixed"
echo "  Changed: $count_changed"
echo "  Removed: $count_removed"
echo "  Other:   $count_other"
echo ""
echo "Done."
