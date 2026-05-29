#!/bin/bash
set -euo pipefail

# ==============================================================================
# 🚀 Changelog Generator Pro
# ==============================================================================

# Default configurations
SINCE=""
DRY_RUN=false
OUTPUT_FILE="CHANGELOG.md"

show_help() {
    echo "======================================================================"
    echo "📖 Changelog Generator Pro - Documentation"
    echo "======================================================================"
    echo "Usage: ./changelog.sh [options]"
    echo ""
    echo "Options:"
    echo "  --since <tag/commit>  Specify starting Git Tag or Commit Hash (default: automatically retrieves the latest Tag)"
    echo "  --dry-run             Preview the generated Changelog without modifying any files"
    echo "  --help                Show this help message"
    echo "======================================================================"
    exit 0
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --since)
            if [[ -n "${2:-}" ]] && [[ ! "$2" == --* ]]; then
                SINCE="$2"
                shift
            else
                echo "❌ Error: --since option requires an argument."
                exit 1
            fi
            ;;
        --dry-run) DRY_RUN=true ;;
        --help) show_help ;;
        *) echo "❌ Unknown option: $1"; show_help ;;
    esac
    shift
done

# Determine Git commit retrieval range
if [ -z "$SINCE" ]; then
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
    if [ -z "$LAST_TAG" ]; then
        RANGE="HEAD"
        TITLE="All Changes"
    else
        RANGE="${LAST_TAG}..HEAD"
        TITLE="Changes since tag **$LAST_TAG**"
    fi
else
    RANGE="${SINCE}..HEAD"
    TITLE="Changes since **$SINCE**"
fi

# Extract Git commit history
COMMITS=$(git log "$RANGE" --pretty=format:"%h %s" 2>/dev/null || true)
if [ -z "$COMMITS" ]; then
    echo "ℹ️ No Git commit records found in range [$RANGE]."
    exit 0
fi

EXISTING_HASHES=""
if [ -f "$OUTPUT_FILE" ]; then
    EXISTING_HASHES=$(grep -oE '\`[a-f0-9]{7,}\`' "$OUTPUT_FILE" | tr -d '\`' || true)
fi

# Initialize categories
BREAKING=""
ADDED=""
FIXED=""
REMOVED=""
CHANGED=""

# Categorize commits based on Conventional Commits or simple heuristics
while IFS= read -r line; do
    [ -z "$line" ] && continue
    hash=$(echo "$line" | awk '{print $1}')
    subject=$(echo "$line" | cut -d' ' -f2-)
    
    # Deduplicate commits already documented in CHANGELOG.md
    if [[ "$EXISTING_HASHES" == *"$hash"* ]]; then
        continue
    fi
    
    type=""
    scope=""
    message=""
    is_breaking=false
    
    # Regex extract: type(!)?(scope)?: message
    pattern="^([a-zA-Z0-9_-]+)(!)?(\(([^)]+)\))?:[[:space:]]*(.*)$"
    if [[ "$subject" =~ $pattern ]]; then
        type="${BASH_REMATCH[1]}"
        if [ "${BASH_REMATCH[2]:-}" == "!" ]; then
            is_breaking=true
        fi
        scope="${BASH_REMATCH[4]:-}"
        message="${BASH_REMATCH[5]:-}"
    else
        # Heuristic fallback matching
        message="$subject"
        if echo "$subject" | grep -iqE "^(feat|add)" >/dev/null 2>&1 || false; then
            type="feat"
        elif echo "$subject" | grep -iqE "^(fix|bug)" >/dev/null 2>&1 || false; then
            type="fix"
        elif echo "$subject" | grep -iqE "^(remove|delete|revert|drop)" >/dev/null 2>&1 || false; then
            type="remove"
        else
            type="chore"
        fi
    fi
    
    # Build clean Markdown message format
    if [ -n "$scope" ]; then
        formatted_msg="- **$scope**: $message (\`$hash\`)"
    else
        formatted_msg="- $message (\`$hash\`)"
    fi
    
    if [ "$is_breaking" = true ] || echo "$message" | grep -q "BREAKING CHANGE" >/dev/null 2>&1 || false; then
        BREAKING="$BREAKING
$formatted_msg"
    else
        # Dispatch to target category
        type_lower=$(echo "$type" | tr '[:upper:]' '[:lower:]')
        case "$type_lower" in
            feat|add)
                ADDED="$ADDED
$formatted_msg"
                ;;
            fix|bug)
                FIXED="$FIXED
$formatted_msg"
                ;;
            remove|delete|revert|drop)
                REMOVED="$REMOVED
$formatted_msg"
                ;;
            *)
                CHANGED="$CHANGED
$formatted_msg"
                ;;
        esac
    fi
done <<< "$COMMITS"

# Compile final Markdown content
NEW_CONTENT="
### $TITLE ($(date '+%Y-%m-%d'))
"

append_section() {
    local header="$1"
    local content="$2"
    
    # Strip empty lines
    local clean_content=$(echo "$content" | sed '/^$/d' || true)
    if [ -n "$clean_content" ]; then
        NEW_CONTENT="$NEW_CONTENT
#### $header
$clean_content
"
    fi
}

append_section "🚨 BREAKING CHANGES" "$BREAKING"
append_section "✨ Added" "$ADDED"
append_section "🐛 Fixed" "$FIXED"
append_section "🗑️ Removed" "$REMOVED"
append_section "⚙️ Changed & Refactored" "$CHANGED"

# Exit early if no new commit content was discovered
if [ $(echo "$NEW_CONTENT" | wc -l) -le 3 ]; then
    echo "ℹ️ No new commit records found to append."
    exit 0
fi

# Handle dry-run preview mode
if [ "$DRY_RUN" = true ]; then
    echo "🔔 [Dry-run Preview Mode] Generated Changelog segment:"
    echo "======================================================================"
    echo -e "$NEW_CONTENT"
    echo "======================================================================"
    exit 0
fi

# Prepend & Inject Mode
if [ -f "$OUTPUT_FILE" ]; then
    EXISTING_CONTENT=$(cat "$OUTPUT_FILE" || true)
    
    # Inject directly below the main # Changelog title if found
    if [[ "$EXISTING_CONTENT" =~ ^#[[:space:]]*[Cc]hangelog(.*)$ ]]; then
        REST="${BASH_REMATCH[1]}"
        printf "# Changelog\n%s\n%s" "$NEW_CONTENT" "$REST" > "$OUTPUT_FILE"
    else
        # Otherwise, simply prepend at the top
        printf "# Changelog\n%s\n\n%s" "$NEW_CONTENT" "$EXISTING_CONTENT" > "$OUTPUT_FILE"
    fi
else
    # Create new file
    printf "# Changelog\n%s" "$NEW_CONTENT" > "$OUTPUT_FILE"
fi

echo "✅ Changelog generated successfully! Prepended increments to $OUTPUT_FILE."
