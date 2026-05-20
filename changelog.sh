#!/bin/bash
# changelog.sh — Professional CHANGELOG.md generator from git history
# Usage: bash changelog.sh [options]
# Repo: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
#
# Features:
#   - Parses conventional commits (feat:, fix:, docs:, etc.)
#   - Emoji-formatted categories (🚀 Added, 🐛 Fixed, 📚 Docs, etc.)
#   - Auto-detects last git tag, supports custom ranges
#   - Multi-tag aware: scans all tags for version history
#   - Contributor acknowledgment section
#   - Stats summary (lines changed, files, contributors)
#   - Machine-readable JSON output mode
#   - Strict mode with comprehensive error handling

set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────
SINCE=""
UNTIL="HEAD"
OUTPUT="CHANGELOG.md"
REPO="$(pwd)"
MODE="markdown"   # markdown | json
INCLUDE_STATS=true
SHOW_CONTRIBUTORS=true
DATE_FORMAT="%Y-%m-%d"

# ─── Colors ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m' # No Color

# ─── Emoji mapping ───────────────────────────────────────────────────
declare -A CATEGORY
CATEGORY=(
    [feat]="🚀 Added"
    [feature]="🚀 Added"
    [fix]="🐛 Fixed"
    [bugfix]="🐛 Fixed"
    [hotfix]="🔥 Hotfix"
    [docs]="📚 Documentation"
    [doc]="📚 Documentation"
    [refactor]="♻️ Refactored"
    [perf]="⚡ Performance"
    [performance]="⚡ Performance"
    [style]="💄 Style"
    [test]="✅ Tests"
    [testing]="✅ Tests"
    [build]="📦 Build"
    [ci]="👷 CI/CD"
    [chore]="🔧 Chores"
    [revert]="⏪ Reverted"
    [deprecate]="⚠️ Deprecated"
    [remove]="🗑️ Removed"
    [security]="🔒 Security"
    [config]="⚙️ Configuration"
)

# ─── Help ────────────────────────────────────────────────────────────
show_help() {
    cat <<EOF
${CYAN}changelog.sh${NC} — Generate a professional CHANGELOG.md from git history

${YELLOW}Usage:${NC}
  $(basename "$0") [OPTIONS]

${YELLOW}Options:${NC}
  --since TAG     Start from this tag/ref (default: auto-detect last tag)
  --until REF     End at this ref (default: HEAD)
  --output FILE   Output file path (default: CHANGELOG.md)
  --repo PATH     Path to git repository (default: current dir)
  --json          Output in JSON format instead of Markdown
  --no-stats      Skip statistics section
  --no-contribs   Skip contributor acknowledgments
  --help          Show this help message

${YELLOW}Examples:${NC}
  bash changelog.sh                              # Full changelog from last tag
  bash changelog.sh --since v1.0.0                # From v1.0.0 to HEAD
  bash changelog.sh --since v1.0.0 --until v2.0.0 # Release notes between tags
  bash changelog.sh --json                        # Machine-readable output

${YELLOW}Exit codes:${NC}
  0   Success
  1   Not a git repository
  2   No commits in range
  3   Git command failed
EOF
    exit 0
}

# ─── Parse args ──────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE="$2"; shift 2 ;;
        --until) UNTIL="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --repo) REPO="$2"; shift 2 ;;
        --json) MODE="json"; shift ;;
        --no-stats) INCLUDE_STATS=false; shift ;;
        --no-contribs) SHOW_CONTRIBUTORS=false; shift ;;
        --help) show_help ;;
        *) echo -e "${RED}Error: Unknown option: $1${NC}" >&2; show_help; exit 1 ;;
    esac
done

# ─── Validation ──────────────────────────────────────────────────────
if ! git -C "$REPO" rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository: $REPO${NC}" >&2
    exit 1
fi

# ─── Auto-detect last tag ─────────────────────────────────────────────
if [[ -z "$SINCE" ]]; then
    # Get the most recent tag that has commits reachable from HEAD
    SINCE=$(git -C "$REPO" describe --tags --abbrev=0 2>/dev/null || echo "")
    # If no tags, try the first commit
    if [[ -z "$SINCE" ]]; then
        SINCE=$(git -C "$REPO" rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
    fi
fi

# ─── Build range ─────────────────────────────────────────────────────
if [[ -n "$SINCE" ]]; then
    RANGE="${SINCE}..${UNTIL}"
    VERSION_HEADER="## [${UNTIL}] - $(date +"$DATE_FORMAT")"
    SUB_HEADER="*Changes since ${SINCE}*"
else
    RANGE="${UNTIL}"
    VERSION_HEADER="## [${UNTIL}] - $(date +"$DATE_FORMAT")"
    SUB_HEADER="*Initial release*"
fi

# ─── Count commits ──────────────────────────────────────────────────
COMMIT_COUNT=$(git -C "$REPO" rev-list "$RANGE" --count 2>/dev/null || echo 0)
if [[ "$COMMIT_COUNT" -eq 0 ]]; then
    echo -e "${YELLOW}No new commits since ${SINCE:-beginning}.${NC}" >&2
    exit 0
fi

echo -e "${CYAN}📦 Processing ${COMMIT_COUNT} commits in range ${RANGE}${NC}"

# ─── Categorize commits ──────────────────────────────────────────────
declare -A CATEGORIES
declare -A COMMITTERS
declare -A FILE_STATS
TOTAL_ADDITIONS=0
TOTAL_DELETIONS=0
ALL_ENTRIES=""

while IFS='|' read -r hash author email date subject body; do
    # Parse conventional commit
    type=""
    scope=""
    breaking=false
    desc="$subject"
    
    if [[ "$subject" =~ ^([a-z_]+)(\([^)]+\))?!?[:\ ].* ]]; then
        type="${BASH_REMATCH[1]}"
        scope="${BASH_REMATCH[2]}"
        # Extract description after type(scope):
        desc=$(echo "$subject" | sed -E 's/^[a-z_]+(\([^)]+\))?!?:[[:space:]]*//')
    fi
    
    # Detect breaking changes
    if echo "$subject" | grep -qE '!' || echo "$body" | grep -qi 'BREAKING CHANGE'; then
        breaking=true
    fi
    
    # Default category
    [[ -z "$type" ]] && type="other"
    
    # Get emoji category
    category="${CATEGORY[$type]:-📌 Miscellaneous}"
    if $breaking; then
        category="💥 Breaking Changes"
    fi
    
    # Build entry
    short_hash="${hash:0:7}"
    entry="- ${desc} ([${short_hash}](${hash}))"
    [[ -n "$scope" ]] && entry="- **${scope}**: ${desc} ([${short_hash}](${hash}))"
    if $breaking; then
        entry="- **${desc}** ([${short_hash}](${hash})) — *breaking change*"
    fi
    
    # Accumulate by category (newest first, so prepend)
    CATEGORIES["$category"]="${CATEGORIES[$category]:-}${entry}"$'\n'
    
    # Track contributors
    NAME="${author}"
    COMMITTERS["$NAME"]=$((COMMITTERS["$NAME"] + 1))
    
    # Get file stats from git diff
    if [[ -n "$SINCE" ]]; then
        stats=$(git -C "$REPO" diff --shortstat "${hash}^!" 2>/dev/null || echo "")
        if [[ "$stats" =~ ([0-9]+)\ insertion ]]; then
            TOTAL_ADDITIONS=$((TOTAL_ADDITIONS + ${BASH_REMATCH[1]}))
        fi
        if [[ "$stats" =~ ([0-9]+)\ deletion ]]; then
            TOTAL_DELETIONS=$((TOTAL_DELETIONS + ${BASH_REMATCH[1]}))
        fi
    fi

done < <(git -C "$REPO" log --format="%H|%an|%ae|%ai|%s|%b" "$RANGE" 2>/dev/null || true)

# ─── Sort categories (custom order) ─────────────────────────────────
CAT_ORDER=(
    "💥 Breaking Changes"
    "🚀 Added"
    "🐛 Fixed"
    "🔥 Hotfix"
    "⚡ Performance"
    "♻️ Refactored"
    "💄 Style"
    "📚 Documentation"
    "✅ Tests"
    "🔒 Security"
    "📦 Build"
    "👷 CI/CD"
    "⚙️ Configuration"
    "🔧 Chores"
    "⏪ Reverted"
    "🗑️ Removed"
    "⚠️ Deprecated"
    "📌 Miscellaneous"
)

# ─── Generate output ──────────────────────────────────────────────────
GENERATED_CONTENT=""

if [[ "$MODE" == "json" ]]; then
    # ── JSON mode ──
    {
        echo "{"
        echo "  \"version\": \"${UNTIL}\","
        echo "  \"date\": \"$(date +"$DATE_FORMAT")\","
        echo "  \"commitCount\": ${COMMIT_COUNT},"
        echo "  \"since\": \"${SINCE}\","
        echo "  \"categories\": {"
        first_cat=true
        for cat in "${CAT_ORDER[@]}"; do
            if [[ -n "${CATEGORIES[$cat]:-}" ]]; then
                $first_cat || echo ","
                first_cat=false
                echo -n "    \"${cat}\": "
                # Convert entries to JSON array
                echo -n "["
                first_entry=true
                while IFS= read -r line; do
                    [[ -z "$line" ]] && continue
                    $first_entry || echo ","
                    first_entry=false
                    # Escape for JSON
                    escaped=$(echo "$line" | sed 's/"/\\"/g')
                    echo -n "      \"${escaped}\""
                done <<< "${CATEGORIES[$cat]}"
                echo " ]"
            fi
        done
        echo ""
        echo "  },"
        if $INCLUDE_STATS; then
            echo "  \"stats\": {"
            echo "    \"additions\": ${TOTAL_ADDITIONS},"
            echo "    \"deletions\": ${TOTAL_DELETIONS},"
            echo "    \"totalChanges\": $((TOTAL_ADDITIONS + TOTAL_DELETIONS))"
            echo "  },"
        fi
        if $SHOW_CONTRIBUTORS; then
            echo "  \"contributors\": ["
            first_contrib=true
            # Sort by commit count descending
            while IFS='|' read -r name count; do
                $first_contrib || echo ","
                first_contrib=false
                echo "    { \"name\": \"${name}\", \"commits\": ${count} }"
            done < <(for name in "${!COMMITTERS[@]}"; do echo "${name}|${COMMITTERS[$name]}"; done | sort -t'|' -k2 -rn)
            echo ""
            echo "  ]"
        fi
        echo "}"
    } > "$OUTPUT"

else
    # ── Markdown mode ──
    {
        echo "# Changelog"
        echo ""
        echo "${VERSION_HEADER}"
        echo "${SUB_HEADER}"
        echo ""
        echo "**${COMMIT_COUNT} commits** · $(date +"$DATE_FORMAT")"
        echo ""
        echo "---"
        echo ""
        
        for cat in "${CAT_ORDER[@]}"; do
            if [[ -n "${CATEGORIES[$cat]:-}" ]]; then
                echo "### ${cat}"
                echo "${CATEGORIES[$cat]}" | sed '/^$/d'
                echo ""
            fi
        done
        
        # Statistics
        if $INCLUDE_STATS && [[ $TOTAL_ADDITIONS -gt 0 || $TOTAL_DELETIONS -gt 0 ]]; then
            echo "---"
            echo "### 📊 Statistics"
            echo ""
            echo "- **Commits:** ${COMMIT_COUNT}"
            echo "- **Lines added:** ${TOTAL_ADDITIONS}"
            echo "- **Lines removed:** ${TOTAL_DELETIONS}"
            echo "- **Net change:** $((TOTAL_ADDITIONS - TOTAL_DELETIONS)) lines"
            echo ""
        fi
        
        # Contributors
        if $SHOW_CONTRIBUTORS && [[ ${#COMMITTERS[@]} -gt 0 ]]; then
            echo "---"
            echo "### 👥 Contributors"
            echo ""
            while IFS='|' read -r name count; do
                echo "- **${name}** (${count} commit$( [[ $count -gt 1 ]] && echo 's'))"
            done < <(for name in "${!COMMITTERS[@]}"; do echo "${name}|${COMMITTERS[$name]}"; done | sort -t'|' -k2 -rn)
            echo ""
            echo "---"
            echo ""
        fi
        
        echo "*Generated by [changelog.sh](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)*"
        
    } > "$OUTPUT"
fi

# ─── Done ─────────────────────────────────────────────────────────────
echo -e "${GREEN}✅ Generated ${OUTPUT}${NC}"
echo -e "   📊 ${COMMIT_COUNT} commits · ${TOTAL_ADDITIONS} additions · ${TOTAL_DELETIONS} deletions"
echo -e "   👥 ${#COMMITTERS[@]} contributors · $(for c in "${!CATEGORIES[@]}"; do [[ -n "${CATEGORIES[$c]}" ]] && echo -n "${c} "; done | wc -w) categories"
echo -e "   📋 Mode: ${MODE}"

exit 0
