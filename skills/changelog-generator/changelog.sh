#!/usr/bin/env bash
set -euo pipefail

# Changelog Generator — Generates structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
# Default output: CHANGELOG.md

OUTPUT="${1:-CHANGELOG.md}"
DATE=$(date +%Y-%m-%d)

# Find latest tag, or use first commit as fallback
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    LATEST_TAG=$(git describe --tags --abbrev=0)
    RANGE="${LATEST_TAG}..HEAD"
    TAG_NOTE="after ${LATEST_TAG}"
else
    FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD | tail -1)
    RANGE="${FIRST_COMMIT}..HEAD"
    TAG_NOTE="from the beginning"
fi

# Collect commits
COMMITS=$(git log "${RANGE}" --pretty=format:"%h|%s|%an" --no-merges 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
    echo "# Changelog" > "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "## ${DATE}" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "No commits found ${TAG_NOTE}." >> "$OUTPUT"
    echo "Generated ${OUTPUT} (no changes found)"
    exit 0
fi

# Categorize commits
declare -A SECTIONS
SECTIONS=(
    ["Added"]=""
    ["Fixed"]=""
    ["Changed"]=""
    ["Removed"]=""
    ["Miscellaneous"]=""
)

while IFS='|' read -r hash subject author; do
    # Skip empty lines
    [ -z "$subject" ] && continue

    lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    entry="- ${subject} (\`${hash}\`)"

    case "$lower_subject" in
        feat:*|feature:*)
            SECTIONS["Added"]+="${entry}"$'\n'
            ;;
        fix:*|bugfix:*|hotfix:*)
            SECTIONS["Fixed"]+="${entry}"$'\n'
            ;;
        refactor:*|perf:*|style:*|chore:*|build:*)
            SECTIONS["Changed"]+="${entry}"$'\n'
            ;;
        remove:*|delete:*)
            SECTIONS["Removed"]+="${entry}"$'\n'
            ;;
        docs:*|doc:*)
            SECTIONS["Added"]+="${entry}"$'\n'
            ;;
        test:*|ci:*|ci)
            SECTIONS["Changed"]+="${entry}"$'\n'
            ;;
        *)
            SECTIONS["Miscellaneous"]+="${entry}"$'\n'
            ;;
    esac
done <<< "$COMMITS"

# Generate output
{
    echo "# Changelog"
    echo ""
    echo "## Unreleased - ${DATE}"
    echo ""
    echo "_Generated from git commits ${TAG_NOTE}._"
    echo ""

    for section in "Added" "Fixed" "Changed" "Removed" "Miscellaneous"; do
        content="${SECTIONS[$section]}"
        if [ -n "$content" ]; then
            echo "### ${section}"
            echo ""
            echo -n "$content"
            echo ""
        fi
    done
} > "$OUTPUT"

echo "Generated ${OUTPUT} ($(echo "$COMMITS" | wc -l | tr -d ' ') commits)"
