#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
TEMP=$(mktemp)

# Determine range: commits since last tag, or all commits
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
    VERSION_HEADER="## [Unreleased] — since \`${LAST_TAG}\`"
else
    RANGE="HEAD"
    VERSION_HEADER="## [Unreleased]"
fi

DATE=$(date +%Y-%m-%d)

# Collect commits by category
added=""
fixed=""
changed=""
removed=""
other=""

while IFS= read -r line; do
    hash=$(echo "$line" | cut -d' ' -f1)
    msg=$(echo "$line" | cut -d' ' -f2-)
    entry="- ${msg} (\`${hash}\`)"

    case "$msg" in
        feat:*|feat\(*|add:*|add\(*)
            added="${added}\n${entry}" ;;
        fix:*|fix\(*|bug:*|bugfix:*)
            fixed="${fixed}\n${entry}" ;;
        chore:*|chore\(*|refactor:*|refactor\(*|perf:*|docs:*|ci:*|build:*)
            changed="${changed}\n${entry}" ;;
        remove:*|remove\(*|revert:*|revert\(*|delete:*)
            removed="${removed}\n${entry}" ;;
        *)
            other="${other}\n${entry}" ;;
    esac
done < <(git log "${RANGE}" --oneline --no-merges 2>/dev/null)

# Build output
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project are documented here."
    echo "Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)."
    echo ""
    echo "---"
    echo ""
    echo "${VERSION_HEADER} — ${DATE}"
    echo ""

    if [ -n "$added" ]; then
        echo "### Added"
        printf "%b\n" "$added"
        echo ""
    fi
    if [ -n "$fixed" ]; then
        echo "### Fixed"
        printf "%b\n" "$fixed"
        echo ""
    fi
    if [ -n "$changed" ]; then
        echo "### Changed"
        printf "%b\n" "$changed"
        echo ""
    fi
    if [ -n "$removed" ]; then
        echo "### Removed"
        printf "%b\n" "$removed"
        echo ""
    fi
    if [ -n "$other" ]; then
        echo "### Other"
        printf "%b\n" "$other"
        echo ""
    fi

    # Append previous content if CHANGELOG already exists
    if [ -f "$OUTPUT" ] && grep -q "^# Changelog" "$OUTPUT" 2>/dev/null; then
        echo "---"
        echo ""
        tail -n +2 "$OUTPUT"
    fi
} > "$TEMP"

mv "$TEMP" "$OUTPUT"
echo "✅ CHANGELOG generated → ${OUTPUT}"
echo "   Range: ${RANGE:-all commits}"
git log "${RANGE}" --oneline --no-merges 2>/dev/null | wc -l | xargs -I{} echo "   Commits processed: {}"
