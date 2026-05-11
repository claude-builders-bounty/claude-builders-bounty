#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: ./changelog.sh [--since <tag>] [--output <file>] [--dry-run]
set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE=""
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help)
            echo "Usage: ./changelog.sh [--since <tag>] [--output <file>] [--dry-run]"
            echo ""
            echo "Generates a structured CHANGELOG.md from git history."
            echo "Auto-categorizes commits into: Added, Fixed, Changed, Removed."
            echo ""
            echo "Options:"
            echo "  --since <tag>   Start from a specific tag (default: last tag)"
            echo "  --output <file> Output file (default: CHANGELOG.md)"
            echo "  --dry-run       Print to stdout instead of writing file"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Must be inside a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not inside a git repository." >&2
    exit 1
fi

# Determine range
if [[ -z "$SINCE" ]]; then
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$LAST_TAG" ]]; then
        RANGE="${LAST_TAG}..HEAD"
        SINCE_DISPLAY="$LAST_TAG"
    else
        # No tags at all — use first commit
        FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
        if [[ -n "$FIRST_COMMIT" ]]; then
            RANGE="${FIRST_COMMIT}..HEAD"
            SINCE_DISPLAY="initial commit"
        else
            RANGE="HEAD"
            SINCE_DISPLAY="HEAD"
        fi
    fi
else
    RANGE="${SINCE}..HEAD"
    SINCE_DISPLAY="$SINCE"
fi

# Get the current version/tag for the heading
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")
CURRENT_DATE=$(date +%Y-%m-%d)

echo "🔍 Scanning commits: $RANGE"

# Fetch all commits in range with format: hash|author|date|message
COMMITS=$(git log "$RANGE" --pretty=format:'%h|%an|%ad|%s' --date=short 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
    echo "ℹ️  No new commits since $SINCE_DISPLAY."
    exit 0
fi

# Categorize commits
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

while IFS='|' read -r hash author date message; do
    # Skip empty lines
    [[ -z "$message" ]] && continue
    
    # Strip trailing whitespace
    message=$(echo "$message" | sed 's/[[:space:]]*$//')
    
    # Categorize by conventional commit prefix
    if echo "$message" | grep -qiE '^(feat|add|new|implement|introduce)'; then
        ADDED+=("- ${message} (${hash}, @${author})")
    elif echo "$message" | grep -qiE '^(fix|bug|patch|resolve|hotfix|correct)'; then
        FIXED+=("- ${message} (${hash}, @${author})")
    elif echo "$message" | grep -qiE '^(remove|drop|delete|deprecate|rm)'; then
        REMOVED+=("- ${message} (${hash}, @${author})")
    elif echo "$message" | grep -qiE '^(chore|refactor|style|docs|test|ci|build|perf|update|change|tweak|improve|upgrade|bump|merge)'; then
        CHANGED+=("- ${message} (${hash}, @${author})")
    else
        # Heuristic: look for keywords in the message
        if echo "$message" | grep -qiE '\b(fix|bug|crash|error|broken|issue)\b'; then
            FIXED+=("- ${message} (${hash}, @${author})")
        elif echo "$message" | grep -qiE '\b(remove|drop|delete|deprecat)\b'; then
            REMOVED+=("- ${message} (${hash}, @${author})")
        elif echo "$message" | grep -qiE '\b(add|new|feature|introduce|support)\b'; then
            ADDED+=("- ${message} (${hash}, @${author})")
        else
            CHANGED+=("- ${message} (${hash}, @${author})")
        fi
    fi
done <<< "$COMMITS"

# Build changelog
build_section() {
    local title="$1"
    shift
    local items=("$@")
    if [[ ${#items[@]} -gt 0 ]]; then
        echo "### $title"
        echo ""
        for item in "${items[@]}"; do
            echo "$item"
        done
        echo ""
    fi
}

generate_changelog() {
    echo "# Changelog"
    echo ""
    echo "## [$CURRENT_TAG] — $CURRENT_DATE"
    echo ""
    echo "_Commits since: ${SINCE_DISPLAY}_"
    echo ""
    build_section "Added" "${ADDED[@]}"
    build_section "Fixed" "${FIXED[@]}"
    build_section "Changed" "${CHANGED[@]}"
    build_section "Removed" "${REMOVED[@]}"
    
    # Stats footer
    TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]}))
    echo "---"
    echo ""
    echo "**Total:** $TOTAL commits — ${#ADDED[@]} added · ${#FIXED[@]} fixed · ${#CHANGED[@]} changed · ${#REMOVED[@]} removed"
}

CHANGELOG_CONTENT=$(generate_changelog)

if $DRY_RUN; then
    echo "$CHANGELOG_CONTENT"
else
    # If CHANGELOG.md exists, prepend new content
    if [[ -f "$OUTPUT" ]]; then
        EXISTING=$(cat "$OUTPUT")
        # Remove the first line (# Changelog) to avoid duplicate title
        NEW_BODY=$(echo "$CHANGELOG_CONTENT" | tail -n +2)
        echo -e "# Changelog\n\n$NEW_BODY\n$EXISTING" > "$OUTPUT"
    else
        echo "$CHANGELOG_CONTENT" > "$OUTPUT"
    fi
    echo "✅ Changelog written to $OUTPUT"
    echo "   ${#ADDED[@]} added · ${#FIXED[@]} fixed · ${#CHANGED[@]} changed · ${#REMOVED[@]} removed"
fi
