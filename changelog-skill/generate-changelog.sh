#!/bin/bash
# generate-changelog - Auto-generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--output FILE] [--tag-prefix v]

set -euo pipefail

OUTPUT="CHANGELOG.md"
TAG_PREFIX="v"

while [[ $# -gt 0 ]]; do
    case $1 in
        --output) OUTPUT="$2"; shift 2;;
        --tag-prefix) TAG_PREFIX="$2"; shift 2;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

LATEST_TAG=$(git describe --tags --abbrev=0 --match "${TAG_PREFIX}*" 2>/dev/null || echo "")
if [ -z "$LATEST_TAG" ]; then
    echo "No tags found. Generating changelog from first commit."
    COMMITS=$(git log --oneline --no-merges)
else
    COMMITS=$(git log "${LATEST_TAG}..HEAD" --oneline --no-merges)
fi

if [ -z "$COMMITS" ]; then
    echo "No commits since last tag."
    exit 0
fi

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## $(git describe --tags --abbrev=0 2>/dev/null || echo 'Unreleased') ($(date +%Y-%m-%d))" >> "$OUTPUT"
echo "" >> "$OUTPUT"

ADDED=""; FIXED=""; CHANGED=""; REMOVED=""; OTHER=""

while IFS= read -r line; do
    msg=$(echo "$line" | cut -d' ' -f2-)
    if echo "$msg" | grep -qiE '^(feat|add)'; then
        ADDED="$ADDED- $msg"$'\n'
    elif echo "$msg" | grep -qiE '^(fix|bug)'; then
        FIXED="$FIXED- $msg"$'\n'
    elif echo "$msg" | grep -qiE '^(chore|refactor|style|perf|ci|build)'; then
        CHANGED="$CHANGED- $msg"$'\n'
    elif echo "$msg" | grep -qiE '^(remove|drop|revert)'; then
        REMOVED="$REMOVED- $msg"$'\n'
    else
        OTHER="$OTHER- $msg"$'\n'
    fi
done <<< "$COMMITS"

[ -n "$ADDED" ] && { echo "### Added" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$ADDED" >> "$OUTPUT"; }
[ -n "$FIXED" ] && { echo "### Fixed" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$FIXED" >> "$OUTPUT"; }
[ -n "$CHANGED" ] && { echo "### Changed" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$CHANGED" >> "$OUTPUT"; }
[ -n "$REMOVED" ] && { echo "### Removed" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$REMOVED" >> "$OUTPUT"; }
[ -n "$OTHER" ] && { echo "### Other" >> "$OUTPUT"; echo "" >> "$OUTPUT"; echo "$OTHER" >> "$OUTPUT"; }

echo "Changelog written to $OUTPUT"
