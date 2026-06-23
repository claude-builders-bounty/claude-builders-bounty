#!/usr/bin/env bash
# changelog.sh - Auto-generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>]
set -euo pipefail

SINCE=""; OUTPUT="CHANGELOG.md"; PREVIOUS_TAG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        *) echo "Usage: $0 [--since <tag>] [--output <file>]"; exit 1 ;;
    esac
done

if [ -z "$SINCE" ]; then
    PREVIOUS_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -n "$PREVIOUS_TAG" ]; then
        SINCE="$PREVIOUS_TAG"
        echo "[changelog] Using tag: $SINCE"
    else
        echo "[changelog] No tags found - generating from first commit"
        SINCE=$(git rev-list --max-parents=0 HEAD)
    fi
fi

{
    echo '# Changelog'
    echo ''
    echo "## [Unreleased]"
    echo ""

    # Added
    ADDED=$(git log "$SINCE..HEAD" --pretty=format:"%s" --grep="^feat" 2>/dev/null || true)
    if [ -n "$ADDED" ]; then
        echo "### Added"
        git log "$SINCE..HEAD" --pretty=format:"- %s (%h)" --grep="^feat" 2>/dev/null
        echo ""
    fi

    # Fixed
    FIXED=$(git log "$SINCE..HEAD" --pretty=format:"%s" --grep="^fix" 2>/dev/null || true)
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        git log "$SINCE..HEAD" --pretty=format:"- %s (%h)" --grep="^fix" 2>/dev/null
        echo ""
    fi

    # Changed
    CHANGED=$(git log "$SINCE..HEAD" --pretty=format:"%s" --grep="^(refactor|perf|style)" -E 2>/dev/null || true)
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        git log "$SINCE..HEAD" --pretty=format:"- %s (%h)" --grep="^(refactor|perf|style)" -E 2>/dev/null
        echo ""
    fi

    # Removed
    REMOVED=$(git log "$SINCE..HEAD" --pretty=format:"%s" --grep="^remove" 2>/dev/null || true)
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        git log "$SINCE..HEAD" --pretty=format:"- %s (%h)" --grep="^remove" 2>/dev/null
        echo ""
    fi

    if [ -n "$PREVIOUS_TAG" ]; then
        echo "---"
        echo ""
        echo "## [$PREVIOUS_TAG]"
        echo "See git log for details."
    fi
} > "$OUTPUT"

echo "[changelog] Generated $OUTPUT with commits since $SINCE"
