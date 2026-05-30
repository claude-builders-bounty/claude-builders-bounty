#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [tag_or_ref]
#   If no argument, uses the latest tag. If no tags exist, uses all commits.

set -euo pipefail

START_REF="${1:-}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "Error: not a git repo" >&2; exit 1; }
OUTPUT="$REPO_ROOT/CHANGELOG.md"

# Step 1: Determine range
if [ -z "$START_REF" ]; then
    START_REF="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [ -n "$START_REF" ]; then
    LOG_RANGE="$START_REF..HEAD"
    HEADER_DATE="$(git log -1 --format='%ad' --date=short "$START_REF" 2>/dev/null || echo "")"
    HEADER_TAG="$START_REF"
    if [ -z "$HEADER_DATE" ]; then
        HEADER_DATE="$(date +%Y-%m-%d)"
    fi
else
    LOG_RANGE="HEAD"
    HEADER_DATE="$(git log -1 --format='%ad' --date=short)"
    HEADER_TAG=""
fi

# Step 2: Fetch commits
TMPFILE="$(mktemp)"
trap 'rm -f "$TMPFILE"' EXIT

git log $LOG_RANGE --pretty=format:"%h|%s|%an|%ad" --date=short > "$TMPFILE" 2>/dev/null || true

TOTAL_LINES=$(wc -l < "$TMPFILE" | tr -d ' ')

if [ "$TOTAL_LINES" -eq 0 ] || [ "$TOTAL_LINES" = "0" ]; then
    echo "No commits found." >&2
    exit 0
fi

# Step 3: Categorize
categorize() {
    local subject="${1,,}"  # lowercase
    if [[ "$subject" =~ ^(add|feat|new|introduce|create|implement) ]]; then echo "Added"
    elif [[ "$subject" =~ ^(fix|bug|patch|resolve|repair|hotfix) ]]; then echo "Fixed"
    elif [[ "$subject" =~ ^(change|update|refactor|improve|bump) ]]; then echo "Changed"
    elif [[ "$subject" =~ ^(remove|delete|drop|deprecate|clean) ]]; then echo "Removed"
    elif [[ "$subject" =~ ^(security|vuln|cve|xss|csrf|inject) ]]; then echo "Security"
    else echo "Other"
    fi
}

declare -A SECTIONS
SECTIONS=( [Added]="" [Fixed]="" [Changed]="" [Removed]="" [Security]="" [Other]="" )

while IFS='|' read -r hash subject author date; do
    [ -z "$hash" ] && continue
    cat="$(categorize "$subject")"
    SECTIONS[$cat]+="- $subject (\`$hash\`) — @$author"$'\n'
done < "$TMPFILE"

# Step 4: Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    if [ -n "$HEADER_TAG" ]; then
        echo "## [$HEADER_TAG] - $HEADER_DATE"
    else
        echo "## $HEADER_DATE"
    fi
    echo ""
    for section in Added Fixed Changed Removed Security Other; do
        if [ -n "${SECTIONS[$section]}" ]; then
            echo "### $section"
            echo -n "${SECTIONS[$section]}"
            echo ""
        fi
    done
} > "$OUTPUT"

# Step 5: Summary
counts=""
for section in Added Fixed Changed Removed Security Other; do
    count=$(echo -n "${SECTIONS[$section]}" | grep -c '^-' || true)
    counts+=" | $section: $count"
done

echo "✅ CHANGELOG.md generated successfully."
echo "  - $TOTAL_LINES commits processed since ${HEADER_TAG:-beginning}"
echo "  -$counts"
echo "  - Output: $OUTPUT"
