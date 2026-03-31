#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: changelog.sh [--since TAG] [--output FILE]
# Acceptance: works via bash, categorizes Added/Fixed/Changed/Removed, outputs Keep a Changelog format

set -euo pipefail

SINCE_TAG=""
OUTPUT="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
    case $1 in
        --since) SINCE_TAG="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: changelog.sh [--since TAG] [--output FILE]"
            echo ""
            echo "Generate CHANGELOG.md from git history since last tag."
            echo ""
            echo "Options:"
            echo "  --since TAG    Start from this tag (default: last tag)"
            echo "  --output FILE  Output file (default: CHANGELOG.md)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Find last tag if not specified
if [[ -z "$SINCE_TAG" ]]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -z "$SINCE_TAG" ]]; then
        echo "⚠️  No tags found. Generating changelog from entire history."
        RANGE=""
    else
        RANGE="${SINCE_TAG}..HEAD"
        echo "📝 Generating changelog from ${SINCE_TAG} to HEAD"
    fi
else
    RANGE="${SINCE_TAG}..HEAD"
    echo "📝 Generating changelog from ${SINCE_TAG} to HEAD"
fi

# Collect commits using null separator for safety
if [[ -z "$RANGE" ]]; then
    git log --pretty=format:"%s" --no-merges > /tmp/_cl_subjects.txt
else
    git log --pretty=format:"%s" --no-merges "$RANGE" > /tmp/_cl_subjects.txt
fi

if [[ ! -s /tmp/_cl_subjects.txt ]]; then
    echo "⚠️  No commits found. Nothing to generate."
    echo "# Changelog" > "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "No changes since ${SINCE_TAG:-initial}." >> "$OUTPUT"
    rm -f /tmp/_cl_subjects.txt
    exit 0
fi

# Also collect short hashes for reference
if [[ -z "$RANGE" ]]; then
    git log --pretty=format:"%h" --no-merges > /tmp/_cl_hashes.txt
else
    git log --pretty=format:"%h" --no-merges "$RANGE" > /tmp/_cl_hashes.txt
fi

# Categorize commits
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

paste /tmp/_cl_hashes.txt /tmp/_cl_subjects.txt | while IFS=$'\t' read -r hash subject; do
    # Detect category from commit prefix (case-insensitive)
    subject_lower="${subject,,}"  # bash 4+ lowercase
    category="other"

    if [[ "$subject_lower" =~ ^(add|feat|feature|new|implement|create|initial|introduce|setup) ]]; then
        category="added"
    elif [[ "$subject_lower" =~ ^(fix|bug|patch|hotfix|resolve|repair|correct) ]]; then
        category="fixed"
    elif [[ "$subject_lower" =~ ^(change|update|refactor|improve|upgrade|bump|modify|rename|move|chore|ci|build|style) ]]; then
        category="changed"
    elif [[ "$subject_lower" =~ ^(remove|delete|deprecate|drop|revert|cleanup|clean) ]]; then
        category="removed"
    fi

    entry="- ${subject} (\`${hash}\`)"
    echo "${category}|||${entry}" >> /tmp/_cl_entries.txt
done

# Get version info
VERSION_TAG="${SINCE_TAG:-Unreleased}"
DATE=$(date +%Y-%m-%d)

# Build output
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/)."
    echo ""
    echo "## [${VERSION_TAG}] — ${DATE}"
    echo ""

    for section in added fixed changed removed other; do
        # Capitalize section name
        display_name="${section^}"
        # Collect entries for this category
        entries=$(grep "^${section}|||" /tmp/_cl_entries.txt 2>/dev/null | sed "s/^${section}|||//" || true)
        if [[ -n "$entries" ]]; then
            echo "### ${display_name}"
            echo ""
            echo "$entries"
            echo ""
        fi
    done
} > "$OUTPUT"

# Count entries
TOTAL=$(wc -l < /tmp/_cl_entries.txt | tr -d '[:space:]')
ADDED_COUNT=$(grep -c "^added|||" /tmp/_cl_entries.txt || true)
FIXED_COUNT=$(grep -c "^fixed|||" /tmp/_cl_entries.txt || true)
CHANGED_COUNT=$(grep -c "^changed|||" /tmp/_cl_entries.txt || true)
REMOVED_COUNT=$(grep -c "^removed|||" /tmp/_cl_entries.txt || true)

echo "✅ Generated ${OUTPUT} with ${TOTAL} entries"
echo "   Added: ${ADDED_COUNT} | Fixed: ${FIXED_COUNT} | Changed: ${CHANGED_COUNT} | Removed: ${REMOVED_COUNT}"

# Cleanup temp files
rm -f /tmp/_cl_subjects.txt /tmp/_cl_hashes.txt /tmp/_cl_entries.txt
