#!/bin/bash
# generate-changelog.sh - Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since-tag] [--output CHANGELOG.md]

set -e

OUTPUT="CHANGELOG.md"
SINCE_TAG=""
REPO_URL=$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' || echo "")
REPO_NAME=$(basename "$REPO_URL" 2>/dev/null || echo "this repository")
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --since-tag)
            SINCE_TAG="$2"
            shift 2
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Determine start point
if [ -z "$SINCE_TAG" ]; then
    if [ -n "$CURRENT_TAG" ]; then
        SINCE_REF="$CURRENT_TAG..HEAD"
        HEADER_LINE="## ${CURRENT_TAG#v} (current)"
    else
        SINCE_REF="HEAD"
        HEADER_LINE="## Unreleased"
    fi
else
    SINCE_REF="$SINCE_TAG..HEAD"
    HEADER_LINE="## ${SINCE_TAG#v}"
fi

# Fetch tags and commits
echo "Generating changelog for $REPO_NAME..."
echo ""

# Temporary files
COMMIT_LOG=$(mktemp)
trap "rm -f $COMMIT_LOG" EXIT

# Get commits with format: type|subject|hash|author_date
git log "$SINCE_REF" --pretty=format:"%s|%H|%aI" --no-merges 2>/dev/null > "$COMMIT_LOG"

# Categorize commits
declare -A CATEGORIES
CATEGORIES=(
    [Added]="Added"
    [Fixed]="Fixed"
    [Changed]="Changed"
    [Removed]="Removed"
    [Security]="Security"
)

declare -A COUNTS
for key in "${!CATEGORIES[@]}"; do
    COUNTS[$key]=0
done

# Process commits
declare -A LINES
for cat in Added Fixed Changed Removed Security; do
    LINES[$cat]=""
done

while IFS='|' read -r subject hash date; do
    [ -z "$subject" ] && continue

    # Categorize by prefix
    lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    category=""
    if echo "$lower_subject" | grep -qE "^(feat|feature|add|new):"; then
        category="Added"
    elif echo "$lower_subject" | grep -qE "^(fix|bugfix|hotfix|patch):"; then
        category="Fixed"
    elif echo "$lower_subject" | grep -qE "^(change|update|upgrade|refactor|improvement):"; then
        category="Changed"
    elif echo "$lower_subject" | grep -qE "^(remove|delete|deprecate):"; then
        category="Removed"
    elif echo "$lower_subject" | grep -qE "^(security|fix security|cve):"; then
        category="Security"
    fi

    if [ -n "$category" ]; then
        short_hash="${hash:0:7}"
        LINES[$category]+="  - $subject (\`$short_hash\`)\n"
        ((COUNTS[$category]++))
    fi
done < "$COMMIT_LOG"

# Write CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to **$REPO_NAME**."
    echo ""
    echo "Generated on $(date '+%Y-%m-%d') by \`generate-changelog.sh\`"
    echo ""
    echo "---"
    echo ""
    echo "$HEADER_LINE"
    echo ""

    total=0
    for cat in Added Fixed Changed Removed Security; do
        count=${COUNTS[$cat]}
        total=$((total + count))
        if [ $count -gt 0 ]; then
            echo "### ${CATEGORIES[$cat]}"
            echo ""
            echo -e "${LINES[$cat]}"
        fi
    done

    if [ $total -eq 0 ]; then
        echo "_No changes since ${CURRENT_TAG:-the beginning of history}_."
    fi

    echo ""
    echo "---"
    echo ""
    echo "_Auto-generated. Edit manually if needed._"
} > "$OUTPUT"

echo "Changelog written to $OUTPUT"
echo ""
echo "Summary:"
for cat in Added Fixed Changed Removed Security; do
    count=${COUNTES[$cat]}
    if [ $count -gt 0 ]; then
        echo "  $cat: $count"
    fi
done
echo ""
echo "Total changes: $total"