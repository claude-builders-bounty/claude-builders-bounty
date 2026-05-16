#!/bin/bash
# changelog.sh — Auto-generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh              # uses latest tag → HEAD
#        bash changelog.sh v1.0.0        # uses v1.0.0 → HEAD
#        bash changelog.sh v1.0.0 v2.0.0 # v1.0.0 → v2.0.0

set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────
REPO_NAME="${1:-$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo 'project')")}"
SINCE_TAG=""
UNTIL="HEAD"
OUTPUT_FILE="CHANGELOG.md"

# ── Parse args ─────────────────────────────────────────────────────────
# If no arguments, auto-detect latest tag
if [ $# -eq 0 ]; then
    # Find the most recent tag reachable from HEAD
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -z "$SINCE_TAG" ]; then
        # No tags — use initial commit
        SINCE_TAG=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
    fi
elif [ $# -eq 1 ]; then
    SINCE_TAG="$1"
elif [ $# -eq 2 ]; then
    SINCE_TAG="$1"
    UNTIL="$2"
fi

SINCE_TAG="${2:-$SINCE_TAG}"

if [ -z "$SINCE_TAG" ]; then
    SINCE_TAG=$(git rev-list --max-parents=0 HEAD)
fi

# ── Color helpers ──────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Generating changelog from ${SINCE_TAG} → ${UNTIL}${NC}"
echo ""

# ── Get commits ────────────────────────────────────────────────────────
COMMITS=$(git log --no-merges --pretty=format:"%H|%s|%an|%ai" "${SINCE_TAG}..${UNTIL}" 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
    echo -e "${YELLOW}⚠️  No new commits since ${SINCE_TAG}${NC}"
    exit 0
fi

# ── Categorize commits ─────────────────────────────────────────────────
CATEGORIES=("Added" "Fixed" "Changed" "Removed" "Deprecated" "Security" "Performance" "Documentation" "Internal")

get_category() {
    local msg="$1"
    local lower="${msg,,}"  # bash 4+: lowercase
    
    # Conventional commits
    if [[ "$lower" =~ ^feat(\(.*\))?!?: ]]; then echo "Added"; return; fi
    if [[ "$lower" =~ ^fix(\(.*\))?!?: ]]; then echo "Fixed"; return; fi
    if [[ "$lower" =~ ^refactor(\(.*\))?!?: ]]; then echo "Changed"; return; fi
    if [[ "$lower" =~ ^perf(\(.*\))?!?: ]]; then echo "Performance"; return; fi
    if [[ "$lower" =~ ^docs?(\(.*\))?!?: ]]; then echo "Documentation"; return; fi
    if [[ "$lower" =~ ^style(\(.*\))?!?: ]]; then echo "Changed"; return; fi
    if [[ "$lower" =~ ^test(\(.*\))?!?: ]]; then echo "Internal"; return; fi
    if [[ "$lower" =~ ^chore(\(.*\))?!?: ]]; then echo "Internal"; return; fi
    if [[ "$lower" =~ ^ci(\(.*\))?!?: ]]; then echo "Internal"; return; fi
    if [[ "$lower" =~ ^build(\(.*\))?!?: ]]; then echo "Internal"; return; fi
    if [[ "$lower" =~ ^revert(\(.*\))?!?: ]]; then echo "Fixed"; return; fi
    
    # Keyword-based fallback
    if [[ "$lower" =~ ^(add|new|create|implement|introduce|support) ]]; then echo "Added"; return; fi
    if [[ "$lower" =~ ^(fix|correct|resolve|patch|hotfix|bug) ]]; then echo "Fixed"; return; fi
    if [[ "$lower" =~ ^(update|change|refactor|revise|improve|migrate) ]]; then echo "Changed"; return; fi
    if [[ "$lower" =~ ^(remove|delete|drop|deprecat) ]]; then echo "Removed"; return; fi
    if [[ "$lower" =~ ^(doc|readme|comment) ]]; then echo "Documentation"; return; fi
    if [[ "$lower" =~ ^(sec|vuln|cve|patch) ]]; then echo "Security"; return; fi
    if [[ "$lower" =~ ^(perf|speed|fast|optimize|latency) ]]; then echo "Performance"; return; fi
    
    # Default
    echo "Changed"
}

declare -A grouped_commits
for cat in "${CATEGORIES[@]}"; do
    grouped_commits["$cat"]=""
done

# Commit count for summary
total=0
added_count=0
fixed_count=0
breaking_count=0

while IFS='|' read -r hash msg author date; do
    [ -z "$hash" ] && continue
    total=$((total + 1))
    
    # Check for breaking changes
    if [[ "$msg" =~ !: ]] || [[ "$msg" =~ BREAKING[-\ ]CHANGE ]]; then
        breaking=$((breaking + 1))
    fi
    
    # Truncate long messages
    if [ ${#msg} -gt 80 ]; then
        msg="${msg:0:80}…"
    fi
    
    cat=$(get_category "$msg")
    entry="  - ${msg} ([${hash:0:7}](https://github.com/${REPO_NAME}/commit/${hash}))"
    
    if [ -z "${grouped_commits["$cat"]}" ]; then
        grouped_commits["$cat"]="$entry"
    else
        grouped_commits["$cat"]="${grouped_commits["$cat"]}"$'\n'"$entry"
    fi
    
    if [ "$cat" = "Added" ]; then added_count=$((added_count + 1)); fi
    if [ "$cat" = "Fixed" ]; then fixed_count=$((fixed_count + 1)); fi
done <<< "$COMMITS"

# ── Generate date ──────────────────────────────────────────────────────
DATE=$(date +%Y-%m-%d)
VERSION=""
if [[ "$SINCE_TAG" =~ ^v?[0-9]+\.[0-9]+\.[0-9] ]]; then
    VERSION="$SINCE_TAG"
fi

# ── Write CHANGELOG.md ────────────────────────────────────────────────
{
    echo "# Changelog"
    echo ""
    
    if [ -n "$VERSION" ]; then
        echo "## [${VERSION}] - ${DATE}"
    else
        echo "## [Unreleased] - ${DATE}"
    fi
    echo ""
    
    # Breaking changes section
    if [ $breaking_count -gt 0 ]; then
        echo "### ⚠️ Breaking Changes"
        echo ""
        echo "  - $breaking_count breaking change(s) introduced"
        echo ""
    fi
    
    # Stats row
    echo "*${total} commits — +${added_count} / !${breaking_count} / ~$((total - added_count - breaking_count))*"
    echo ""
    
    # Categorized entries
    for cat in "${CATEGORIES[@]}"; do
        entries="${grouped_commits["$cat"]}"
        if [ -n "$entries" ]; then
            echo "### ${cat}"
            echo ""
            echo "$entries"
            echo ""
        fi
    done
    
    echo "---"
    echo ""
    echo "*Generated by [changelog.sh](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)*"
    
} > "$OUTPUT_FILE"

echo -e "${GREEN}✅ Written ${total} commits to ${OUTPUT_FILE}${NC}"
echo ""
echo -e "  ${GREEN}+${NC} Added: ${added_count}"
echo -e "  ${RED}✗${NC} Fixed: ${fixed_count}"
echo -e "  ${YELLOW}~${NC} Changed: $((total - added_count - fixed_count))"
echo -e "  ${PURPLE}⚠${NC} Breaking: ${breaking_count}"
echo ""
echo -e "${BLUE}📄 ${OUTPUT_FILE}${NC}"
