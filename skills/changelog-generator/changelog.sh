#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh              # Commits since last tag
#   bash changelog.sh v1.0.0       # Commits since v1.0.0
#   bash changelog.sh --all        # All commits
#
# Output: CHANGELOG.md in the current directory.

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────

VERSION_TAG="${1:-}"
OUTPUT_FILE="CHANGELOG.md"
DATE=$(date +%Y-%m-%d)

# ── Determine commit range ───────────────────────────────────────────────

if [ "$VERSION_TAG" = "--all" ]; then
    RANGE=""
    SINCE_DESC="all commits"
elif [ -n "$VERSION_TAG" ]; then
    RANGE="${VERSION_TAG}..HEAD"
    SINCE_DESC="since $VERSION_TAG"
else
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -n "$LATEST_TAG" ]; then
        RANGE="${LATEST_TAG}..HEAD"
        SINCE_DESC="since $LATEST_TAG"
    else
        RANGE=""
        SINCE_DESC="all commits"
    fi
fi

# ── Fetch commits ────────────────────────────────────────────────────────

if [ -n "$RANGE" ]; then
    COMMITS=$(git log "$RANGE" --pretty=format:"%s|||%an|||%h" --no-merges 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%s|||%an|||%h" --no-merges 2>/dev/null || echo "")
fi

if [ -z "$COMMITS" ]; then
    echo "No commits found ($SINCE_DESC). Nothing to generate."
    exit 0
fi

# ── Categorize commits ──────────────────────────────────────────────────

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
    msg=$(echo "$line" | awk -F'\\|\\|\\|' '{print $1}')
    author=$(echo "$line" | awk -F'\\|\\|\\|' '{print $2}')
    hash=$(echo "$line" | awk -F'\\|\\|\\|' '{print $3}')

    # Normalize: lowercase first word for matching
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

    entry="- ${msg} (\`${hash}\`) — *${author}*"

    # Categorize based on conventional commit prefixes and keywords
    case "$lower_msg" in
        feat:*|feat\(*|add:*|add\ *|added\ *|new:*|new\ *|implement*|create*|introduce*)
            ADDED="${ADDED}${entry}\n"
            ;;
        fix:*|fix\(*|bugfix*|hotfix*|patch:*|resolve*|repair*)
            FIXED="${FIXED}${entry}\n"
            ;;
        remove*|delete*|deprecat*|drop\ *|uninstall*)
            REMOVED="${REMOVED}${entry}\n"
            ;;
        refactor*|chore*|update*|upgrade*|change*|improve*|enhance*|migrate*|rename*|move*|style*|perf*|ci:*|ci\(*|build:*|build\(*|docs:*|docs\(*|test:*|test\(*)
            CHANGED="${CHANGED}${entry}\n"
            ;;
        *)
            # Try keyword-based categorization
            if echo "$lower_msg" | grep -qiE 'add|creat|new|introduc|implement|support'; then
                ADDED="${ADDED}${entry}\n"
            elif echo "$lower_msg" | grep -qiE 'fix|bug|resolv|repair|patch|correct'; then
                FIXED="${FIXED}${entry}\n"
            elif echo "$lower_msg" | grep -qiE 'remov|delet|deprecat|drop|strip'; then
                REMOVED="${REMOVED}${entry}\n"
            elif echo "$lower_msg" | grep -qiE 'updat|chang|refactor|improv|enhanc|migrat|renam|mov|upgrad'; then
                CHANGED="${CHANGED}${entry}\n"
            else
                OTHER="${OTHER}${entry}\n"
            fi
            ;;
    esac
done <<< "$COMMITS"

# ── Generate CHANGELOG.md ───────────────────────────────────────────────

{
    REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
    NEXT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || true)
    if [ -z "$NEXT_VERSION" ]; then
        NEXT_VERSION="Unreleased"
    else
        NEXT_VERSION=$(echo "$NEXT_VERSION" | sed 's/^v//')
    fi
    
    echo "# Changelog"
    echo ""
    echo "All notable changes to **${REPO_NAME}** are documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
    echo ""
    echo "## [${NEXT_VERSION}] — ${DATE}"
    echo ""
    echo "_Generated ${SINCE_DESC}_"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo ""
        echo -e "$ADDED"
    fi
    
    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo ""
        echo -e "$FIXED"
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo ""
        echo -e "$CHANGED"
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo ""
        echo -e "$REMOVED"
    fi
    
    if [ -n "$OTHER" ]; then
        echo "### Other"
        echo ""
        echo -e "$OTHER"
    fi

} > "$OUTPUT_FILE"

# ── Summary ──────────────────────────────────────────────────────────────

TOTAL=$(echo "$COMMITS" | wc -l)
count_entries() { if [ -z "$1" ]; then echo 0; else echo -e "$1" | grep -c '^-' || echo 0; fi; }
echo "Generated $OUTPUT_FILE ($SINCE_DESC, $TOTAL commits)"
echo "  Added=$(count_entries "$ADDED") Fixed=$(count_entries "$FIXED") Changed=$(count_entries "$CHANGED") Removed=$(count_entries "$REMOVED") Other=$(count_entries "$OTHER")"
