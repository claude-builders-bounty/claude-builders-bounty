#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# generate-changelog.sh
# Auto-generate structured CHANGELOG.md from git history
# ============================================================

VERSION="1.0.0"
OUTPUT_FILE="CHANGELOG.md"
APPEND_MODE=false
RANGE=""
MAX_COMMITS=500

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# --- Parse args ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --append|-a) APPEND_MODE=true; shift ;;
        --output|-o) OUTPUT_FILE="$2"; shift 2 ;;
        --max|-m) MAX_COMMITS="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: changelog.sh [OPTIONS] [RANGE]"
            echo ""
            echo "Options:"
            echo "  -a, --append     Append to existing CHANGELOG.md"
            echo "  -o, --output     Output file (default: CHANGELOG.md)"
            echo "  -m, --max        Max commits to process (default: 500)"
            echo "  -h, --help       Show this help"
            echo ""
            echo "Range:"
            echo "  v1.0.0..v1.1.0  Specific tag range"
            echo "  v1.0.0..        From tag to HEAD"
            echo "  (auto)          Last tag to HEAD, or all commits if no tags"
            exit 0
            ;;
        *) RANGE="$1"; shift ;;
    esac
done

# --- Verify git repo ---
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo -e "${RED}Error: Not inside a git repository${NC}" >&2
    exit 1
fi

REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")

# --- Determine range ---
if [[ -z "$RANGE" ]]; then
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$LATEST_TAG" ]]; then
        # Check if there are commits since the tag
        COMMITS_SINCE_TAG=$(git rev-list "${LATEST_TAG}..HEAD" --count 2>/dev/null || echo "0")
        if [[ "$COMMITS_SINCE_TAG" -gt 0 ]]; then
            RANGE="${LATEST_TAG}..HEAD"
            FROM_REF="$LATEST_TAG"
        else
            # Tag is at HEAD, use last 2 tags
            PREV_TAG=$(git tag --sort=-version:refname | sed -n '2p' 2>/dev/null || echo "")
            if [[ -n "$PREV_TAG" ]]; then
                RANGE="${PREV_TAG}..${LATEST_TAG}"
                FROM_REF="$PREV_TAG"
            else
                # Only one tag, show all commits
                RANGE=""
                FROM_REF="initial commit"
            fi
        fi
    else
        # No tags at all, show all commits
        RANGE=""
        FROM_REF="initial commit"
    fi
fi

TO_REF="HEAD"

echo -e "${BLUE}📋 Generating changelog for ${REPO_NAME}${NC}"
if [[ -n "$RANGE" ]]; then
    echo -e "   Range: ${RANGE}"
else
    echo -e "   Range: all commits"
fi
echo ""

# --- Extract commits ---
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a DOCS=()
declare -a MAINT=()
declare -a OTHER=()

# Build git log command
LOG_CMD=(git log --pretty=format:'%h|%an|%ad|%s' --date=short -n "$MAX_COMMITS")
if [[ -n "$RANGE" ]]; then
    LOG_CMD+=("$RANGE")
fi

while IFS='|' read -r hash author date message; do
    # Skip merge commits
    [[ "$message" =~ ^Merge\  ]] && continue
    
    # Trim whitespace
    message=$(echo "$message" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [[ -z "$message" ]] && continue
    
    # Short hash
    short_hash="${hash:0:7}"
    
    # Entry format
    entry="- ${message} (\`${short_hash}\`)"
    
    # Categorize by conventional commit prefix or keywords
    lower_msg="${message,,}"
    
    if [[ "$lower_msg" =~ ^(feat|add|new|create|implement|support|Introduce) ]]; then
        ADDED+=("$entry")
    elif [[ "$lower_msg" =~ ^(fix|bug|patch|resolve|correct|repair|hotfix|hot-fix) ]]; then
        FIXED+=("$entry")
    elif [[ "$lower_msg" =~ ^(remove|delete|deprecate|drop|eliminate) ]]; then
        REMOVED+=("$entry")
    elif [[ "$lower_msg" =~ ^(refactor|update|change|modify|improve|perf|optimize|rename|move|migrate|enhance) ]]; then
        CHANGED+=("$entry")
    elif [[ "$lower_msg" =~ ^(docs?|readme|changelog) ]]; then
        DOCS+=("$entry")
    elif [[ "$lower_msg" =~ ^(chore|ci|build|test|deps?|bump|release|version) ]]; then
        MAINT+=("$entry")
    else
        OTHER+=("$entry")
    fi
done < <("${LOG_CMD[@]}" 2>/dev/null || true)

# --- Build output ---
TODAY=$(date +%Y-%m-%d)
TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#DOCS[@]} + ${#MAINT[@]} + ${#OTHER[@]}))

if [[ $TOTAL -eq 0 ]]; then
    echo -e "${YELLOW}⚠ No commits found in range${NC}"
    exit 0
fi

# Build the changelog content
CHANGELOG="## [Unreleased] - ${TODAY}\n\n"

if [[ ${#ADDED[@]} -gt 0 ]]; then
    CHANGELOG+="### ✨ Added\n"
    for item in "${ADDED[@]}"; do
        CHANGELOG+="${item}\n"
    done
    CHANGELOG+="\n"
fi

if [[ ${#FIXED[@]} -gt 0 ]]; then
    CHANGELOG+="### 🐛 Fixed\n"
    for item in "${FIXED[@]}"; do
        CHANGELOG+="${item}\n"
    done
    CHANGELOG+="\n"
fi

if [[ ${#CHANGED[@]} -gt 0 ]]; then
    CHANGELOG+="### 🔄 Changed\n"
    for item in "${CHANGED[@]}"; do
        CHANGELOG+="${item}\n"
    done
    CHANGELOG+="\n"
fi

if [[ ${#REMOVED[@]} -gt 0 ]]; then
    CHANGELOG+="### 🗑️ Removed\n"
    for item in "${REMOVED[@]}"; do
        CHANGELOG+="${item}\n"
    done
    CHANGELOG+="\n"
fi

if [[ ${#DOCS[@]} -gt 0 ]]; then
    CHANGELOG+="### 📚 Documentation\n"
    for item in "${DOCS[@]}"; do
        CHANGELOG+="${item}\n"
    done
    CHANGELOG+="\n"
fi

if [[ ${#MAINT[@]} -gt 0 ]]; then
    CHANGELOG+="### 🔧 Maintenance\n"
    for item in "${MAINT[@]}"; do
        CHANGELOG+="${item}\n"
    done
    CHANGELOG+="\n"
fi

if [[ ${#OTHER[@]} -gt 0 ]]; then
    CHANGELOG+="### 📦 Other\n"
    for item in "${OTHER[@]}"; do
        CHANGELOG+="${item}\n"
    done
    CHANGELOG+="\n"
fi

# Write output
if [[ "$APPEND_MODE" == true ]] && [[ -f "$OUTPUT_FILE" ]]; then
    # Insert new content after the first line
    {
        head -1 "$OUTPUT_FILE"
        echo ""
        echo -e "$CHANGELOG"
        tail -n +2 "$OUTPUT_FILE"
    } > "${OUTPUT_FILE}.tmp"
else
    {
        echo "# Changelog"
        echo ""
        echo -e "$CHANGELOG"
        # Preserve existing content if any
        if [[ -f "$OUTPUT_FILE" ]]; then
            tail -n +2 "$OUTPUT_FILE" 2>/dev/null || true
        fi
    } > "${OUTPUT_FILE}.tmp"
fi

mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"

echo -e "${GREEN}✅ Generated ${OUTPUT_FILE} with ${TOTAL} entries${NC}"
echo ""
echo "   ✨ Added:        ${#ADDED[@]}"
echo "   🐛 Fixed:        ${#FIXED[@]}"
echo "   🔄 Changed:      ${#CHANGED[@]}"
echo "   🗑️ Removed:      ${#REMOVED[@]}"
echo "   📚 Documentation: ${#DOCS[@]}"
echo "   🔧 Maintenance:  ${#MAINT[@]}"
echo "   📦 Other:        ${#OTHER[@]}"
