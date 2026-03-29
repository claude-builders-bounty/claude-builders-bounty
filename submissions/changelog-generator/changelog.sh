#!/bin/bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# By sami (sami-openlife) — autonomous AI agent
# 
# Usage: bash changelog.sh [output_file]
# Default output: CHANGELOG.md in current directory

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

# Get the last tag, or use initial commit if no tags
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
TAG_DATE=$(git log -1 --format=%ai "$LAST_TAG" 2>/dev/null | cut -d' ' -f1)
CURRENT_DATE=$(date +%Y-%m-%d)

# Get current version from tag or default
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    LAST_TAG_NAME=$(git describe --tags --abbrev=0)
    RANGE="${LAST_TAG_NAME}..HEAD"
    HEADER="## [Unreleased] (since ${LAST_TAG_NAME})"
else
    RANGE=""
    HEADER="## [Unreleased]"
fi

# Categorize commits using conventional commit prefixes and keywords
categorize() {
    local msg="$1"
    local lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    # Conventional commits
    if echo "$lower" | grep -qE '^feat[:(]|^add[:(]|\badd(ed|s)?\b.*\b(support|feature|option|endpoint|integration)\b'; then
        echo "Added"
    elif echo "$lower" | grep -qE '^fix[:(]|^bug[:(]|\bfix(ed|es)?\b|\bbug\b|\bresolve[ds]?\b|\bpatch\b'; then
        echo "Fixed"
    elif echo "$lower" | grep -qE '^remove[:(]|^delete[:(]|\bremov(e[ds]?|ing)\b|\bdelet(e[ds]?|ing)\b|\bdrop(ped|s)?\b|\bdeprecate[ds]?\b'; then
        echo "Removed"
    elif echo "$lower" | grep -qE '^refactor[:(]|^chore[:(]|^style[:(]|^perf[:(]|^docs[:(]|^ci[:(]|^build[:(]|^test[:(]|\bupdat(e[ds]?|ing)\b|\brefactor\b|\bimprov(e[ds]?|ing)\b|\bchange[ds]?\b|\bmigrat(e[ds]?|ing)\b|\brenam(e[ds]?|ing)\b|\breplace[ds]?\b|\bupgrad(e[ds]?|ing)\b'; then
        echo "Changed"
    else
        echo "Changed"
    fi
}

# Collect commits
declare -A ADDED FIXED CHANGED REMOVED
added_list=""
fixed_list=""
changed_list=""
removed_list=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    
    # Strip conventional commit prefix for cleaner display
    clean_msg=$(echo "$line" | sed -E 's/^(feat|fix|chore|refactor|style|perf|docs|ci|build|test|remove|delete)(\([^)]*\))?[: ]*//')
    # Capitalize first letter
    clean_msg="$(echo "${clean_msg:0:1}" | tr '[:lower:]' '[:upper:]')${clean_msg:1}"
    
    category=$(categorize "$line")
    
    case "$category" in
        Added)   added_list="${added_list}- ${clean_msg}\n" ;;
        Fixed)   fixed_list="${fixed_list}- ${clean_msg}\n" ;;
        Changed) changed_list="${changed_list}- ${clean_msg}\n" ;;
        Removed) removed_list="${removed_list}- ${clean_msg}\n" ;;
    esac
done < <(git log ${RANGE} --pretty=format:"%s" --no-merges)

# Generate CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
    echo ""
    echo "${HEADER}"
    echo ""
    
    if [ -n "$added_list" ]; then
        echo "### Added"
        echo -e "$added_list"
    fi
    
    if [ -n "$fixed_list" ]; then
        echo "### Fixed"
        echo -e "$fixed_list"
    fi
    
    if [ -n "$changed_list" ]; then
        echo "### Changed"
        echo -e "$changed_list"
    fi
    
    if [ -n "$removed_list" ]; then
        echo "### Removed"
        echo -e "$removed_list"
    fi
    
} > "$OUTPUT"

echo "✅ Generated ${OUTPUT}"
echo ""
cat "$OUTPUT"
