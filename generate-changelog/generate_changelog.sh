#!/usr/bin/env bash
# =====================================================================
#  generate_changelog.sh — Auto-generate CHANGELOG.md from git history
# =====================================================================
#  Usage:
#    chmod +x generate_changelog.sh
#    ./generate_changelog.sh [output_file] [tag_range]
#
#  Examples:
#    ./generate_changelog.sh                    # generates CHANGELOG.md
#    ./generate_changelog.sh CHANGELOG.md v1.0  # from v1.0 to HEAD
# =====================================================================

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
RANGE="${2:-}"

# Determine tag range
if [ -z "$RANGE" ]; then
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [ -z "$LAST_TAG" ]; then
        echo "No tags found — generating changelog for all commits."
        RANGE="HEAD"
    else
        RANGE="${LAST_TAG}..HEAD"
        echo "Using tag range: $RANGE"
    fi
fi

# Fetch commits
COMMITS=$(git log --format="%H|%s" "$RANGE" 2>/dev/null) || {
    echo "Error: invalid range or no commits found" >&2
    exit 1
}

if [ -z "$COMMITS" ]; then
    echo "No new commits since $RANGE."
    echo "# Changelog" > "$OUTPUT"
    echo "" >> "$OUTPUT"
    echo "No changes." >> "$OUTPUT"
    exit 0
fi

# Categorize commits
CATEGORIES="Added|Fixed|Changed|Removed|Deprecated|Security|Performance|Documentation"
INIT_COMMIT="^[0-9a-f]+\|Initial commit"

declare -A grouped
grouped["Added"]=""
grouped["Fixed"]=""
grouped["Changed"]=""
grouped["Removed"]=""
grouped["Deprecated"]=""
grouped["Security"]=""
grouped["Performance"]=""
grouped["Documentation"]=""
grouped["Other"]=""

while IFS="|" read -r hash msg; do
    # Skip merge commits and initial commit
    echo "$msg" | grep -qi "^merge " && continue
    echo "$msg" | grep -qi "^initial commit" && continue
    
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    categorized=false
    
    for cat in Added Fixed Changed Removed Deprecated Security Performance Documentation; do
        lower_cat=$(echo "$cat" | tr '[:upper:]' '[:lower:]')
        if echo "$lower_msg" | grep -qE "^($lower_cat|$lower_cat\(|feat|fix|perf|docs|refactor|chore|style|test|build|ci|revert)"; then
            # Map conventional commit types
            case "$lower_msg" in
                feat*)  grouped["Added"]+="  - ${msg}  \n";;
                fix*)   grouped["Fixed"]+="  - ${msg}  \n";;
                perf*)  grouped["Performance"]+="  - ${msg}  \n";;
                docs*)  grouped["Documentation"]+="  - ${msg}  \n";;
                $lower_cat*) grouped["$cat"]+="  - ${msg}  \n";;
                *)      grouped["$cat"]+="  - ${msg}  \n";;
            esac
            categorized=true
            break
        fi
    done
    
    if ! $categorized; then
        grouped["Other"]+="  - ${msg}  \n"
    fi
done <<< "$COMMITS"

# Generate output
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")
DATE=$(date +%Y-%m-%d)

{
    echo "# Changelog"
    echo ""
    echo "## [$VERSION] - $DATE"
    echo ""
    
    any_content=false
    for cat in Added Fixed Changed Removed Deprecated Security Performance Documentation Other; do
        items="${grouped[$cat]}"
        if [ -n "$items" ]; then
            any_content=true
            echo "### $cat"
            echo -e "$items"
            echo ""
        fi
    done
    
    if ! $any_content; then
        echo "No significant changes in this release."
        echo ""
    fi
} > "$OUTPUT"

echo "✓ CHANGELOG generated at: $OUTPUT"
echo "  Categories: $(echo "$grouped" | tr ' ' '\n' | grep -c .)"
