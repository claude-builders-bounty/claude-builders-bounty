#!/usr/bin/env bash
# ============================================================
# changelog.sh — Structured CHANGELOG generator from git history
# ============================================================
# Usage:
#   ./changelog.sh                    # Generate CHANGELOG for current repo
#   ./changelog.sh --since v1.0.0     # From a specific tag
#   ./changelog.sh --output RELEASE.md # Custom output file
#   ./changelog.sh --limit 50          # Limit commit count
#
# Zero dependencies. Auto-categorizes commits into:
#   Added | Fixed | Changed | Removed
# ============================================================

set -euo pipefail

# ─── Configuration ─────────────────────────────────────────

OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
COMMIT_LIMIT=100
REPO_PATH="."

# ─── Argument Parsing ──────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --output|-o)
            OUTPUT_FILE="$2"; shift 2 ;;
        --since|-s)
            SINCE_TAG="$2"; shift 2 ;;
        --limit|-n)
            COMMIT_LIMIT="$2"; shift 2 ;;
        --help|-h)
            cat << 'HELP'
Usage: changelog.sh [OPTIONS]

Generate a structured CHANGELOG.md from git history.
Auto-categorizes commits into Added, Fixed, Changed, Removed.

Options:
  -o, --output FILE   Output file (default: CHANGELOG.md)
  -s, --since TAG     Start from git tag (default: last tag)
  -n, --limit N       Max commits to process (default: 100)
  -h, --help          Show this help

Examples:
  ./changelog.sh
  ./changelog.sh --since v1.0.0 --output RELEASE.md
  ./changelog.sh --limit 200
HELP
            exit 0 ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1 ;;
    esac
done

# ─── Detect Git Range ──────────────────────────────────────

cd "$REPO_PATH"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: Not a git repository" >&2
    exit 1
fi

if [[ -z "$SINCE_TAG" ]]; then
    # Try to find the last tag
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE_TAG" ]]; then
    RANGE="${SINCE_TAG}..HEAD"
    TAG_NAME="$SINCE_TAG"
    VERSION_HEADER="## [Unreleased]"
else
    RANGE="HEAD"
    TAG_NAME=""
    VERSION_HEADER="## [Unreleased]"
fi

# ─── Fetch Commits ─────────────────────────────────────────

echo "📋 Analyzing commits since ${SINCE_TAG:-beginning}..."

# Get commits: hash|date|author|message
COMMITS=$(git log "$RANGE" --no-merges --format="%h|%as|%an|%s" -n "$COMMIT_LIMIT" 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
    echo "⚠️  No commits found in range: $RANGE"
    # Still generate an empty CHANGELOG
    cat > "$OUTPUT_FILE" << 'EOF'
# Changelog

## [Unreleased]

_No changes yet._
EOF
    echo "✅ Empty CHANGELOG written to $OUTPUT_FILE"
    exit 0
fi

# ─── Categorize Commits ────────────────────────────────────

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

while IFS='|' read -r hash date author message; do
    # Trim whitespace
    message=$(echo "$message" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    # Determine category from conventional commit prefix
    category="other"
    display_msg="$message"
    
    # Check conventional commit prefixes using grep
    if echo "$message" | grep -qiE '^(feat|feature|add|added)[(:]'; then
        category="added"
        display_msg=$(echo "$message" | sed -E 's/^(feat|feature|add|added)[(:] *//i')
    elif echo "$message" | grep -qiE '^(fix|bug|hotfix|patch)[(:]'; then
        category="fixed"
        display_msg=$(echo "$message" | sed -E 's/^(fix|bug|hotfix|patch)[(:] *//i')
    elif echo "$message" | grep -qiE '^(refactor|perf|style|chore|ci|build|test|docs|revert)[(:]'; then
        category="changed"
        display_msg=$(echo "$message" | sed -E 's/^(refactor|perf|style|chore|ci|build|test|docs|revert)[(:] *//i')
    elif echo "$message" | grep -qiE '^(remove|delete|drop|deprecate)[(:]'; then
        category="removed"
        display_msg=$(echo "$message" | sed -E 's/^(remove|delete|drop|deprecate)[(:] *//i')
    fi
    
    # Fallback: keyword matching in message
    if [[ "$category" == "other" ]]; then
        if echo "$message" | grep -qiE '\b(fix|bug|resolve|patch|hotfix)\b'; then
            category="fixed"
        elif echo "$message" | grep -qiE '\b(add|new|introduce|implement|create)\b'; then
            category="added"
        elif echo "$message" | grep -qiE '\b(remove|delete|drop|deprecate)\b'; then
            category="removed"
        elif echo "$message" | grep -qiE '\b(update|change|refactor|improve|bump|upgrade|migrate)\b'; then
            category="changed"
        fi
    fi
    
    entry="- ${display_msg} (${hash})"
    
    case "$category" in
        added)   ADDED+=("$entry") ;;
        fixed)   FIXED+=("$entry") ;;
        changed) CHANGED+=("$entry") ;;
        removed) REMOVED+=("$entry") ;;
        *)       OTHER+=("$entry") ;;
    esac
done <<< "$COMMITS"

# ─── Generate CHANGELOG ─────────────────────────────────────

TODAY=$(date +%Y-%m-%d)

{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "$VERSION_HEADER"
    echo ""

    # Added
    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        printf '%s\n' "${ADDED[@]}"
        echo ""
    fi

    # Fixed
    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        printf '%s\n' "${FIXED[@]}"
        echo ""
    fi

    # Changed
    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        printf '%s\n' "${CHANGED[@]}"
        echo ""
    fi

    # Removed
    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        printf '%s\n' "${REMOVED[@]}"
        echo ""
    fi

    # Other (uncategorized)
    if [[ ${#OTHER[@]} -gt 0 ]]; then
        echo "### Other"
        printf '%s\n' "${OTHER[@]}"
        echo ""
    fi

    # Footer
    echo "---"
    echo ""
    echo "_Generated on ${TODAY} from ${COMMIT_LIMIT} commits._"

} > "$OUTPUT_FILE"

# ─── Summary ───────────────────────────────────────────────

echo ""
echo "✅ CHANGELOG generated: $OUTPUT_FILE"
echo "   Added:   ${#ADDED[@]} commits"
echo "   Fixed:   ${#FIXED[@]} commits"
echo "   Changed: ${#CHANGED[@]} commits"
echo "   Removed: ${#REMOVED[@]} commits"
echo "   Other:   ${#OTHER[@]} commits"
echo "   ─────────────────────"
echo "   Total:   $((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]})) commits"
