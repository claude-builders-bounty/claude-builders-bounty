#!/usr/bin/env bash
# generate-changelog.sh — Structured CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [--tag v1.0.0] [--output CHANGELOG.md]
#
# Fetches commits since the last git tag, auto-categorizes them into
# Added / Fixed / Changed / Removed, and writes CHANGELOG.md.
#
# Also works as Claude Code skill: copy to .claude/commands/generate-changelog.md
# or invoke via /generate-changelog in Claude Code.

set -euo pipefail

OUTPUT="${OUTPUT:-CHANGELOG.md}"
SINCE_TAG="${SINCE_TAG:-}"

# ── Parse args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --tag) SINCE_TAG="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: bash generate-changelog.sh [--tag v1.0.0] [--output CHANGELOG.md]"
            echo ""
            echo "Generates a structured CHANGELOG.md from git commits since the last tag."
            echo "Auto-categorizes commits into: Added, Fixed, Changed, Removed."
            exit 0
            ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# ── Determine the range ─────────────────────────────────────────────────────
if [[ -z "$SINCE_TAG" ]]; then
    # Get the most recent tag
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -z "$SINCE_TAG" ]]; then
    # No tags at all — use all commits
    RANGE="HEAD"
    TAG_DISPLAY="Initial release"
else
    RANGE="${SINCE_TAG}..HEAD"
    TAG_DISPLAY="$SINCE_TAG"
fi

# ── Get version ─────────────────────────────────────────────────────────────
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")
if [[ "$VERSION" == "$SINCE_TAG" ]]; then
    VERSION="Unreleased"
fi
DATE=$(date +%Y-%m-%d)

# ── Fetch commits ───────────────────────────────────────────────────────────
COMMITS=$(git log "$RANGE" --no-merges --pretty=format:"%s" 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
    echo "No commits found since $TAG_DISPLAY."
    exit 0
fi

# ── Categorization ──────────────────────────────────────────────────────────
# Uses conventional commit prefixes and keyword heuristics
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    # Strip bullet points and leading whitespace
    clean=$(echo "$line" | sed 's/^[*-]\s*//' | sed 's/^\s*//')

    # Categorize by conventional commit prefix
    if echo "$clean" | grep -qiE '^(feat|add|create|implement|introduce)\b'; then
        ADDED+=("$clean")
    elif echo "$clean" | grep -qiE '^(fix|bug|hotfix|patch|resolve|correct)\b'; then
        FIXED+=("$clean")
    elif echo "$clean" | grep -qiE '^(remove|drop|delete|deprecate)\b'; then
        REMOVED+=("$clean")
    elif echo "$clean" | grep -qiE '^(chore|refactor|update|upgrade|bump|change|modify|adjust|improve|optimize|tweak|style|perf|ci|build|test|docs)\b'; then
        CHANGED+=("$clean")
    elif echo "$clean" | grep -qiE '^(fix|bug)'; then
        FIXED+=("$clean")
    elif echo "$clean" | grep -qiE '^(add|feat)'; then
        ADDED+=("$clean")
    else
        # Heuristic fallback: keyword matching
        if echo "$clean" | grep -qiE '\b(fix|bug|issue|crash|error|broken)\b'; then
            FIXED+=("$clean")
        elif echo "$clean" | grep -qiE '\b(add|new|feature)\b'; then
            ADDED+=("$clean")
        elif echo "$clean" | grep -qiE '\b(remov|delet|drop|deprecat)\b'; then
            REMOVED+=("$clean")
        else
            CHANGED+=("$clean")
        fi
    fi
done <<< "$COMMITS"

# ── Generate CHANGELOG.md ───────────────────────────────────────────────────
{
    echo "# Changelog"
    echo ""
    echo "## [$VERSION] — $DATE"
    echo ""

    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        for item in "${ADDED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        for item in "${FIXED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        for item in "${CHANGED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        for item in "${REMOVED[@]}"; do
            echo "- $item"
        done
        echo ""
    fi

    echo "> Generated from $TAG_DISPLAY to HEAD ($(echo "$COMMITS" | wc -l | tr -d ' ') commits)"
} > "$OUTPUT"

echo "✓ CHANGELOG.md generated: $VERSION"
echo "  Added:   ${#ADDED[@]} entries"
echo "  Fixed:   ${#FIXED[@]} entries"
echo "  Changed: ${#CHANGED[@]} entries"
echo "  Removed: ${#REMOVED[@]} entries"
echo "  Output:  $OUTPUT"
