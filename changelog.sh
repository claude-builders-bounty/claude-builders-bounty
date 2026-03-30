#!/bin/bash
# changelog.sh - Generate CHANGELOG.md from git history
# Usage: bash changelog.sh

PROJECT_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo '.')")
OUTPUT_FILE="CHANGELOG.md"

# Detect version from last tag
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

get_commits() {
    if [ -n "$VERSION" ]; then
        git log "$VERSION..HEAD" --pretty=format:"%s|||%b" 2>/dev/null || echo ""
    else
        git log --pretty=format:"%s|||%b" 2>/dev/null || echo ""
    fi
}

categorize() {
    local msg="$1"
    local body="${2:-}"
    local combined="$msg $body"
    local lmsg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    if echo "$lmsg" | grep -qiE '^(feat|add)[\>:]'; then
        echo "ADDED"
    elif echo "$lmsg" | grep -qiE '^(fix|bug|patch)[\>:]'; then
        echo "FIXED"
    elif echo "$lmsg" | grep -qiE '^(remove|delete|deprecate)[\>:]'; then
        echo "REMOVED"
    elif echo "$lmsg" | grep -qiE '^(chore|ci|docs|refactor|perf|test|style)[\>:]'; then
        echo "CHANGED"
    else
        echo "CHANGED"
    fi
}

# Temp file for commits
COMMITS_TMP=$(mktemp)
get_commits > "$COMMITS_TMP"

# Build changelog
{
    echo "# Changelog"
    echo ""
    
    # Version header
    if [ -n "$VERSION" ]; then
        echo "## $PROJECT_NAME $VERSION"
    else
        echo "## $PROJECT_NAME (unreleased)"
    fi
    echo ""
    echo "All notable changes are documented here."
    echo ""
    
    for section in "Added" "Fixed" "Changed" "Removed"; do
        echo "### $section"
        echo ""
        while IFS='|||' read -r msg body; do
            [ -z "$msg" ] && continue
            type=$(categorize "$msg" "$body")
            section_key=$(echo "$section" | tr '[:upper:]' '[:lower:]')
            [ "$type" = "$section_key" ] && echo "- $msg"
        done < "$COMMITS_TMP"
        echo ""
    done
    
} > "$OUTPUT_FILE"

rm -f "$COMMITS_TMP"

count=$(grep -c '^- ' "$OUTPUT_FILE" 2>/dev/null || echo 0)
echo "✅ CHANGELOG.md generated with $count entries"
