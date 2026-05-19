#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh                    (commits since last tag)
#        bash changelog.sh <since> [<until>]  (custom range)
#
# Categorizes commits by conventional commit prefixes:
#   feat/feature → Added
#   fix/bugfix   → Fixed
#   refactor     → Changed
#   remove/drop  → Removed
#   Others       → Other

set -euo pipefail

# ── Config ──────────────────────────────────────────────
OUTPUT="${OUTPUT:-CHANGELOG.md}"
SINCE="${1:-}"
UNTIL="${2:-HEAD}"

# ── Determine range ────────────────────────────────────
if [ -z "$SINCE" ]; then
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -z "$LAST_TAG" ]; then
        # No tags — use all commits
        SINCE=$(git rev-list --max-parents=0 HEAD)
        RANGE="$SINCE..$UNTIL"
    else
        RANGE="$LAST_TAG..$UNTIL"
    fi
else
    RANGE="$SINCE..$UNTIL"
fi

# ── Fetch commits ──────────────────────────────────────
COMMITS=$(git log --pretty=format:"%h|%s|%an|%ad" --date=short "$RANGE" 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    echo "No commits found in range $RANGE"
    exit 0
fi

# ── Categorize ─────────────────────────────────────────
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

while IFS='|' read -r hash subject author date; do
    # Skip merge commits
    if [[ "$subject" =~ ^Merge ]]; then
        continue
    fi
    # Clean subject: strip conventional commit prefix
    clean=$(echo "$subject" | sed -E 's/^(feat|feature|fix|bugfix|refactor|style|test|docs|ci|build|chore|perf|remove|drop|revert)[\(\!]*:?\s*//')

    if [[ "$subject" =~ ^feat|^feature ]]; then
        ADDED+=("- $clean ($hash) — $author, $date")
    elif [[ "$subject" =~ ^fix|^bugfix ]]; then
        FIXED+=("- $clean ($hash) — $author, $date")
    elif [[ "$subject" =~ ^refactor|^perf ]]; then
        CHANGED+=("- $clean ($hash) — $author, $date")
    elif [[ "$subject" =~ ^remove|^drop ]]; then
        REMOVED+=("- $clean ($hash) — $author, $date")
    else
        OTHER+=("- $clean ($hash) — $author, $date")
    fi
done <<< "$COMMITS"

# ── Generate CHANGELOG ───────────────────────────────
TAG_CURRENT=$(git describe --tags --abbrev=0 2>/dev/null || echo "HEAD")
TODAY=$(date +%Y-%m-%d)
RANGE_LABEL="$RANGE"

{
    echo "# Changelog"
    echo ""
    echo "## $TAG_CURRENT — $TODAY"
    echo ""

    [ ${#ADDED[@]} -gt 0 ] && {
        echo "### ✨ Added"
        echo ""
        printf '%s\n' "${ADDED[@]}"
        echo ""
    }

    [ ${#FIXED[@]} -gt 0 ] && {
        echo "### 🐛 Fixed"
        echo ""
        printf '%s\n' "${FIXED[@]}"
        echo ""
    }

    [ ${#CHANGED[@]} -gt 0 ] && {
        echo "### 🔧 Changed"
        echo ""
        printf '%s\n' "${CHANGED[@]}"
        echo ""
    }

    [ ${#REMOVED[@]} -gt 0 ] && {
        echo "### 🗑️ Removed"
        echo ""
        printf '%s\n' "${REMOVED[@]}"
        echo ""
    }

    [ ${#OTHER[@]} -gt 0 ] && {
        echo "### 📝 Other"
        echo ""
        printf '%s\n' "${OTHER[@]}"
        echo ""
    }

} > "$OUTPUT"

TOTAL=${#ADDED[@]}
TOTAL=$((TOTAL + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]}))

echo "✅ CHANGELOG.md generated ($TOTAL commits from $RANGE_LABEL)"
echo "   Written to: $OUTPUT"
