#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# changelog.sh — Generate a structured CHANGELOG.md from git history
# ──────────────────────────────────────────────────────────────────────────────
#
# Usage:
#   bash changelog.sh                  # Generate from last tag to HEAD
#   bash changelog.sh --all            # Generate from all history
#   bash changelog.sh --since v1.2.0   # Generate from specific tag
#   bash changelog.sh --output out.md  # Write to custom file
#
# Categories commits into: Added, Fixed, Changed, Removed
# based on conventional commit prefixes and keyword analysis.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
ALL_HISTORY=false
REPO_URL=""

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)       ALL_HISTORY=true; shift ;;
        --since)     SINCE_TAG="$2"; shift 2 ;;
        --output)    OUTPUT_FILE="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: bash changelog.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --all            Generate from entire git history"
            echo "  --since TAG      Generate from a specific tag"
            echo "  --output FILE    Write to custom file (default: CHANGELOG.md)"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ── Validate git repo ────────────────────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "❌ Error: Not inside a git repository."
    exit 1
fi

# ── Detect repo URL ──────────────────────────────────────────────────────────
REPO_URL=$(git config --get remote.origin.url 2>/dev/null || echo "")
REPO_URL=$(echo "$REPO_URL" | sed -E 's/\.git$//' | sed -E 's#git@github\.com:#https://github.com/#')

# ── Determine range ──────────────────────────────────────────────────────────
if [ "$ALL_HISTORY" = true ]; then
    RANGE=""
    RANGE_DESC="all history"
elif [ -n "$SINCE_TAG" ]; then
    RANGE="${SINCE_TAG}..HEAD"
    RANGE_DESC="since ${SINCE_TAG}"
else
    # Auto-detect last tag
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -n "$LAST_TAG" ]; then
        RANGE="${LAST_TAG}..HEAD"
        RANGE_DESC="since ${LAST_TAG}"
    else
        RANGE=""
        RANGE_DESC="all history (no tags found)"
    fi
fi

echo "📝 Generating changelog ($RANGE_DESC)..."

# ── Fetch commits ─────────────────────────────────────────────────────────────
if [ -n "$RANGE" ]; then
    COMMITS=$(git log "$RANGE" --pretty=format:"%H|||%s|||%an|||%as" --no-merges 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%H|||%s|||%an|||%as" --no-merges 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
    echo "ℹ️  No commits found for the specified range."
    exit 0
fi

# ── Categorize commits ───────────────────────────────────────────────────────
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

categorize_commit() {
    local hash="$1"
    local subject="$2"
    local author="$3"
    local date="$4"
    local short_hash="${hash:0:7}"

    # Build commit link if repo URL is available
    local commit_ref="$short_hash"
    if [ -n "$REPO_URL" ]; then
        commit_ref="[\`${short_hash}\`](${REPO_URL}/commit/${hash})"
    fi

    local entry="- ${subject} (${commit_ref}) — *${author}*"

    # Lowercase subject for matching
    local lower_subject
    lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

    # Category detection based on conventional commits + keywords
    case "$lower_subject" in
        feat:*|feat\(*|add:*|add\ *|added\ *|new:*|new\ *|implement*|create*|introduce*)
            ADDED="${ADDED}${entry}\n"
            ;;
        fix:*|fix\(*|fix\ *|fixed\ *|bugfix*|hotfix*|patch:*|resolve*|repair*)
            FIXED="${FIXED}${entry}\n"
            ;;
        remove*|delete*|deprecat*|drop\ *|rm\ *|clean\ up*|cleanup*)
            REMOVED="${REMOVED}${entry}\n"
            ;;
        refactor*|change*|update*|modify*|improve*|enhance*|optimize*|perf*|style*|chore*|build*|ci*|docs*|test*|rename*|move*|migrate*|upgrade*|bump*)
            CHANGED="${CHANGED}${entry}\n"
            ;;
        *)
            # Keyword-based fallback
            if echo "$lower_subject" | grep -qE '(add|new|creat|implement|introduc|support)'; then
                ADDED="${ADDED}${entry}\n"
            elif echo "$lower_subject" | grep -qE '(fix|bug|resolv|repair|patch|correct)'; then
                FIXED="${FIXED}${entry}\n"
            elif echo "$lower_subject" | grep -qE '(remov|delet|deprecat|drop|strip)'; then
                REMOVED="${REMOVED}${entry}\n"
            else
                CHANGED="${CHANGED}${entry}\n"
            fi
            ;;
    esac
}

# Process each commit
while IFS= read -r line; do
    [ -z "$line" ] && continue
    hash=$(echo "$line" | awk -F'\\|\\|\\|' '{print $1}')
    subject=$(echo "$line" | awk -F'\\|\\|\\|' '{print $2}')
    author=$(echo "$line" | awk -F'\\|\\|\\|' '{print $3}')
    date=$(echo "$line" | awk -F'\\|\\|\\|' '{print $4}')
    categorize_commit "$hash" "$subject" "$author" "$date"
done <<< "$COMMITS"

# ── Generate CHANGELOG ───────────────────────────────────────────────────────
VERSION_HEADER=""
if [ -n "$SINCE_TAG" ]; then
    VERSION_HEADER="## [Unreleased] — $(date +%Y-%m-%d) (${RANGE_DESC})"
elif git describe --tags --abbrev=0 &>/dev/null; then
    NEXT_TAG="Unreleased"
    LAST_TAG=$(git describe --tags --abbrev=0)
    VERSION_HEADER="## [${NEXT_TAG}] — $(date +%Y-%m-%d) (since ${LAST_TAG})"
else
    VERSION_HEADER="## [Unreleased] — $(date +%Y-%m-%d)"
fi

{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    echo ""
    echo "$VERSION_HEADER"
    echo ""

    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo -e "$ADDED"
    fi

    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo -e "$FIXED"
    fi

    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo -e "$CHANGED"
    fi

    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo -e "$REMOVED"
    fi

} > "$OUTPUT_FILE"

# ── Summary ───────────────────────────────────────────────────────────────────
TOTAL=$(echo "$COMMITS" | wc -l | tr -d ' ')
ADDED_COUNT=$(echo -e "$ADDED" | grep -c "^-" || true)
FIXED_COUNT=$(echo -e "$FIXED" | grep -c "^-" || true)
CHANGED_COUNT=$(echo -e "$CHANGED" | grep -c "^-" || true)
REMOVED_COUNT=$(echo -e "$REMOVED" | grep -c "^-" || true)

echo ""
echo "✅ Generated $OUTPUT_FILE"
echo "   📊 $TOTAL commits categorized:"
echo "      ✨ Added:   $ADDED_COUNT"
echo "      🐛 Fixed:   $FIXED_COUNT"
echo "      🔄 Changed: $CHANGED_COUNT"
echo "      🗑️  Removed: $REMOVED_COUNT"
echo ""
