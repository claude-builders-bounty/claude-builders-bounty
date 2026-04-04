#!/bin/bash

# CHANGELOG Generator - Automatically generates structured CHANGELOG.md from git history
# Supports Markdown and JSON output formats with conventional commit categorization
#
# Usage:
#   ./changelog.sh [options] [output_file]
#
# Options:
#   --format=md|json    Output format (default: md)
#   --since=<tag|date>  Only include commits since tag or date (e.g. v1.0.0, 2026-01-01)
#   --all               Include all commits (ignore tags)
#   --help              Show this help message
#
# Examples:
#   ./changelog.sh                           # Markdown to stdout
#   ./changelog.sh CHANGELOG.md              # Markdown to file
#   ./changelog.sh --format=json             # JSON to stdout
#   ./changelog.sh --format=json changes.json
#   ./changelog.sh --since=v1.0.0            # Since specific tag
#   ./changelog.sh --since=2026-01-01        # Since specific date

set -e

# ─── Defaults ───────────────────────────────────────────────────────────────
FORMAT="md"
SINCE=""
INCLUDE_ALL=false
OUTPUT_FILE=""

# ─── Parse arguments ────────────────────────────────────────────────────────
show_help() {
    sed -n '2,/^$/p' "$0" | sed 's/^# \?//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --format=*)  FORMAT="${1#*=}" ;;
        --since=*)   SINCE="${1#*=}" ;;
        --all)       INCLUDE_ALL=true ;;
        --help|-h)   show_help ;;
        -*)          echo "Unknown option: $1" >&2; exit 1 ;;
        *)           OUTPUT_FILE="$1" ;;
    esac
    shift
done

# Validate format
if [[ "$FORMAT" != "md" && "$FORMAT" != "json" ]]; then
    echo "Error: Invalid format '$FORMAT'. Use 'md' or 'json'." >&2
    exit 1
fi

# Ensure we are in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Error: Not inside a git repository." >&2
    exit 1
fi

TEMP_FILE=$(mktemp)
trap 'rm -f "$TEMP_FILE"' EXIT

# ─── Determine commit range ────────────────────────────────────────────────
if [ -n "$SINCE" ]; then
    # Check if SINCE looks like a date (YYYY-MM-DD)
    if [[ "$SINCE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        COMMIT_RANGE="--since=$SINCE"
        VERSION_LABEL="Changes since $SINCE"
    else
        # Treat as a tag/ref
        if git rev-parse "$SINCE" &>/dev/null; then
            COMMIT_RANGE="$SINCE..HEAD"
            VERSION_LABEL="Changes since $SINCE"
        else
            echo "Error: Tag or ref '$SINCE' not found." >&2
            exit 1
        fi
    fi
elif [ "$INCLUDE_ALL" = true ]; then
    COMMIT_RANGE=""
    VERSION_LABEL="All Changes"
else
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -n "$LAST_TAG" ]; then
        COMMIT_RANGE="$LAST_TAG..HEAD"
        VERSION_LABEL=$(git describe --tags --exact-match HEAD 2>/dev/null || echo "Unreleased (since $LAST_TAG)")
    else
        COMMIT_RANGE=""
        VERSION_LABEL="Unreleased"
    fi
fi

# ─── Fetch commits ─────────────────────────────────────────────────────────
if [[ "$COMMIT_RANGE" == --since=* ]]; then
    ALL_COMMITS=$(git log --oneline --reverse "$COMMIT_RANGE" 2>/dev/null || echo "")
elif [ -n "$COMMIT_RANGE" ]; then
    ALL_COMMITS=$(git log --oneline --reverse "$COMMIT_RANGE" 2>/dev/null || echo "")
else
    ALL_COMMITS=$(git log --oneline --reverse 2>/dev/null || echo "")
fi

# ─── Categorize commits (7 categories) ─────────────────────────────────────
declare -a CAT_FEAT=()      # Features / Added
declare -a CAT_FIX=()       # Bug Fixes
declare -a CAT_DOCS=()      # Documentation
declare -a CAT_STYLE=()     # Styling / Formatting
declare -a CAT_REFACTOR=()  # Refactoring
declare -a CAT_TEST=()      # Tests
declare -a CAT_CHORE=()     # Chores / Maintenance
declare -a CAT_OTHER=()     # Uncategorized

while IFS= read -r commit; do
    [ -z "$commit" ] && continue
    
    # Extract hash and message
    hash=$(echo "$commit" | cut -d' ' -f1)
    msg=$(echo "$commit" | cut -d' ' -f2-)
    msg_lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    # Match conventional commit prefix first (e.g. "feat:", "fix(scope):")
    # Then fall back to keyword matching
    if [[ "$msg_lower" =~ ^feat[(:\ ] ]] || [[ "$msg_lower" =~ ^feature[(:\ ] ]] || \
       [[ "$msg_lower" =~ ^add[(:\ ] ]] || [[ "$msg_lower" == *"add "* ]] || \
       [[ "$msg_lower" == *"new "* ]] || [[ "$msg_lower" == *"create "* ]] || \
       [[ "$msg_lower" == *"implement"* ]]; then
        CAT_FEAT+=("$hash|$msg")
    
    elif [[ "$msg_lower" =~ ^fix[(:\ ] ]] || [[ "$msg_lower" =~ ^bug[(:\ ] ]] || \
         [[ "$msg_lower" =~ ^patch[(:\ ] ]] || [[ "$msg_lower" == *"fix "* ]] || \
         [[ "$msg_lower" == *"bug "* ]] || [[ "$msg_lower" == *"resolve "* ]]; then
        CAT_FIX+=("$hash|$msg")
    
    elif [[ "$msg_lower" =~ ^docs?[(:\ ] ]] || [[ "$msg_lower" == *"readme"* ]] || \
         [[ "$msg_lower" == *"documentation"* ]] || [[ "$msg_lower" == *"changelog"* ]] || \
         [[ "$msg_lower" == *"license"* ]]; then
        CAT_DOCS+=("$hash|$msg")
    
    elif [[ "$msg_lower" =~ ^style[(:\ ] ]] || [[ "$msg_lower" == *"format"* ]] || \
         [[ "$msg_lower" == *"lint"* ]] || [[ "$msg_lower" == *"whitespace"* ]] || \
         [[ "$msg_lower" == *"styling"* ]]; then
        CAT_STYLE+=("$hash|$msg")
    
    elif [[ "$msg_lower" =~ ^refactor[(:\ ] ]] || [[ "$msg_lower" =~ ^perf[(:\ ] ]] || \
         [[ "$msg_lower" == *"refactor"* ]] || [[ "$msg_lower" == *"restructure"* ]] || \
         [[ "$msg_lower" == *"optimize"* ]] || [[ "$msg_lower" == *"performance"* ]]; then
        CAT_REFACTOR+=("$hash|$msg")
    
    elif [[ "$msg_lower" =~ ^test[(:\ ] ]] || [[ "$msg_lower" == *"test"* ]] || \
         [[ "$msg_lower" == *"spec "* ]] || [[ "$msg_lower" == *"coverage"* ]]; then
        CAT_TEST+=("$hash|$msg")
    
    elif [[ "$msg_lower" =~ ^chore[(:\ ] ]] || [[ "$msg_lower" =~ ^ci[(:\ ] ]] || \
         [[ "$msg_lower" =~ ^build[(:\ ] ]] || [[ "$msg_lower" == *"dependency"* ]] || \
         [[ "$msg_lower" == *"dependencies"* ]] || [[ "$msg_lower" == *"bump "* ]] || \
         [[ "$msg_lower" == *"release"* ]] || [[ "$msg_lower" == *"merge"* ]]; then
        CAT_CHORE+=("$hash|$msg")
    
    else
        CAT_OTHER+=("$hash|$msg")
    fi
done <<< "$ALL_COMMITS"

# ─── Emoji map ──────────────────────────────────────────────────────────────
declare -A EMOJI_MAP=(
    [Features]="✨"
    [Bug Fixes]="🐛"
    [Documentation]="📝"
    [Styling]="💄"
    [Refactoring]="♻️"
    [Tests]="✅"
    [Chores]="🔧"
    [Other]="📦"
)

# ─── Output: Markdown ───────────────────────────────────────────────────────
output_markdown() {
    echo "# Changelog" > "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    echo "## $VERSION_LABEL" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    
    local has_content=false
    
    write_md_section() {
        local title="$1"
        shift
        local entries=("$@")
        if [ ${#entries[@]} -gt 0 ]; then
            local emoji="${EMOJI_MAP[$title]}"
            echo "### ${emoji} ${title}" >> "$TEMP_FILE"
            echo "" >> "$TEMP_FILE"
            for entry in "${entries[@]}"; do
                local hash="${entry%%|*}"
                local msg="${entry#*|}"
                # Strip conventional commit prefix for cleaner output
                msg=$(echo "$msg" | sed -E 's/^(feat|fix|docs?|style|refactor|perf|test|chore|ci|build)(\([^)]*\))?[: ]+//i')
                echo "- ${msg} (\`${hash}\`)" >> "$TEMP_FILE"
            done
            echo "" >> "$TEMP_FILE"
            has_content=true
        fi
    }
    
    write_md_section "Features"      "${CAT_FEAT[@]}"
    write_md_section "Bug Fixes"     "${CAT_FIX[@]}"
    write_md_section "Documentation" "${CAT_DOCS[@]}"
    write_md_section "Styling"       "${CAT_STYLE[@]}"
    write_md_section "Refactoring"   "${CAT_REFACTOR[@]}"
    write_md_section "Tests"         "${CAT_TEST[@]}"
    write_md_section "Chores"        "${CAT_CHORE[@]}"
    write_md_section "Other"         "${CAT_OTHER[@]}"
    
    if [ "$has_content" = false ]; then
        echo "No changes since last release." >> "$TEMP_FILE"
        echo "" >> "$TEMP_FILE"
    fi
}

# ─── Output: JSON ───────────────────────────────────────────────────────────
output_json() {
    local first_cat=true
    
    json_array() {
        local entries=("$@")
        local first=true
        echo -n "["
        for entry in "${entries[@]}"; do
            local hash="${entry%%|*}"
            local msg="${entry#*|}"
            msg=$(echo "$msg" | sed -E 's/^(feat|fix|docs?|style|refactor|perf|test|chore|ci|build)(\([^)]*\))?[: ]+//i')
            # Escape JSON special characters
            msg=$(echo "$msg" | sed 's/\\/\\\\/g; s/"/\\"/g')
            if [ "$first" = true ]; then first=false; else echo -n ","; fi
            echo -n "{\"hash\":\"$hash\",\"message\":\"$msg\"}"
        done
        echo -n "]"
    }
    
    {
        echo "{"
        echo "  \"version\": \"$VERSION_LABEL\","
        echo "  \"generated\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
        echo "  \"categories\": {"
        
        write_json_cat() {
            local name="$1"
            shift
            local entries=("$@")
            if [ ${#entries[@]} -gt 0 ]; then
                if [ "$first_cat" = true ]; then first_cat=false; else echo ","; fi
                echo -n "    \"$name\": "
                json_array "${entries[@]}"
            fi
        }
        
        write_json_cat "features"      "${CAT_FEAT[@]}"
        write_json_cat "bug_fixes"     "${CAT_FIX[@]}"
        write_json_cat "documentation" "${CAT_DOCS[@]}"
        write_json_cat "styling"       "${CAT_STYLE[@]}"
        write_json_cat "refactoring"   "${CAT_REFACTOR[@]}"
        write_json_cat "tests"         "${CAT_TEST[@]}"
        write_json_cat "chores"        "${CAT_CHORE[@]}"
        write_json_cat "other"         "${CAT_OTHER[@]}"
        
        echo ""
        echo "  },"
        
        # Summary stats
        local total=$((${#CAT_FEAT[@]} + ${#CAT_FIX[@]} + ${#CAT_DOCS[@]} + ${#CAT_STYLE[@]} + ${#CAT_REFACTOR[@]} + ${#CAT_TEST[@]} + ${#CAT_CHORE[@]} + ${#CAT_OTHER[@]}))
        echo "  \"stats\": {"
        echo "    \"total\": $total,"
        echo "    \"features\": ${#CAT_FEAT[@]},"
        echo "    \"bug_fixes\": ${#CAT_FIX[@]},"
        echo "    \"documentation\": ${#CAT_DOCS[@]},"
        echo "    \"styling\": ${#CAT_STYLE[@]},"
        echo "    \"refactoring\": ${#CAT_REFACTOR[@]},"
        echo "    \"tests\": ${#CAT_TEST[@]},"
        echo "    \"chores\": ${#CAT_CHORE[@]},"
        echo "    \"other\": ${#CAT_OTHER[@]}"
        echo "  }"
        echo "}"
    } > "$TEMP_FILE"
}

# ─── Generate output ────────────────────────────────────────────────────────
case "$FORMAT" in
    md)   output_markdown ;;
    json) output_json ;;
esac

# ─── Write output ───────────────────────────────────────────────────────────
if [ -z "$OUTPUT_FILE" ]; then
    cat "$TEMP_FILE"
else
    mv "$TEMP_FILE" "$OUTPUT_FILE"
    echo "✅ Changelog written to $OUTPUT_FILE ($FORMAT format)"
fi
