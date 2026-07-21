#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>]
set -euo pipefail
SINCE_TAG=""
OUTPUT="CHANGELOG.md"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE_TAG="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done
if [ -z "$SINCE_TAG" ]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi
COMMITS=""
if [ -n "$SINCE_TAG" ]; then
    COMMITS=$(git log "$SINCE_TAG"..HEAD --pretty=format:"%s" 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%s" 2>/dev/null || echo "")
fi
echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## [Unreleased]" >> "$OUTPUT"
echo "" >> "$OUTPUT"
ADDED=""; FIXED=""; CHANGED=""; REMOVED=""
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    case "$line" in
        *[Aa]dd*|*[Ff]eat*) ADDED="${ADDED}- $line\n" ;;
        *[Ff]ix*|*[Bb]ug*)  FIXED="${FIXED}- $line\n" ;;
        *[Rr]emove*|*[Dd]el*) REMOVED="${REMOVED}- $line\n" ;;
        *) CHANGED="${CHANGED}- $line\n" ;;
    esac
done <<< "$COMMITS"
for CAT in "Added:$ADDED" "Fixed:$FIXED" "Changed:$CHANGED" "Removed:$REMOVED"; do
    NAME="${CAT%%:*}"; ENTRIES="${CAT#*:}"
    if [ -n "$ENTRIES" ]; then
        echo "### $NAME" >> "$OUTPUT"
        printf "%b" "$ENTRIES" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
done
echo "CHANGELOG generated: $(wc -l < "$OUTPUT") lines"
