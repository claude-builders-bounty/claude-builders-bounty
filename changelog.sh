#!/bin/bash
# changelog.sh — Generate CHANGELOG.md from git history
# Usage: bash changelog.sh [repo_path]
# Defaults to current directory if no path given.

set -e

REPO="${1:-.}"
cd "$REPO"

# Get the previous tag (if any)
PREV_TAG=$(git describe --tags --abbrev=0 HEAD~1 2>/dev/null || echo "")
CURRENT_TAG=$(git describe --tags --abbrev=0 HEAD 2>/dev/null || echo "")

DATE=$(date +%Y-%m-%d)

# Header
echo "# Changelog"
echo

if [[ -n "$CURRENT_TAG" ]]; then
    echo "## [$CURRENT_TAG] - $DATE"
else
    echo "## [Unreleased] - $DATE"
fi
echo

# Collect commits since last tag
COMMITS=$(git log --format="%s" $PREV_TAG..HEAD 2>/dev/null | grep -v "^Merge" || true)

declare -A categories
categories["Added"]=""
categories["Fixed"]=""
categories["Changed"]=""
categories["Removed"]=""

process_commit() {
    local msg="$1"
    local type=$(echo "$msg" | head -1 | cut -d: -f1 | xargs)
    local body=$(echo "$msg" | cut -d: -f2- | xargs)

    case "$type" in
        feat|feature|add)
            categories["Added"]+="- $body\n"
            ;;
        fix|bug|patch)
            categories["Fixed"]+="- $body\n"
            ;;
        refactor|perf|chore|docs|style|test|build)
            categories["Changed"]+="- $body\n"
            ;;
        remove|delete|deprecate)
            categories["Removed"]+="- $body\n"
            ;;
        *)
            if [[ -n "$msg" ]]; then
                categories["Changed"]+="- $msg\n"
            fi
            ;;
    esac
}

while IFS= read -r line; do
    process_commit "$line"
done <<< "$COMMITS"

print_section() {
    local label="$1"
    local content="${categories[$label]}"
    if [[ -n "$content" ]]; then
        echo "### $label"
        echo -e "$content"
    fi
}

print_section "Added"
print_section "Fixed"
print_section "Changed"
print_section "Removed"

# If no content, note it
if [[ -z "${categories[Added]}${categories[Fixed]}${categories[Changed]}${categories[Removed]}" ]]; then
    echo "No categorized changes found since $PREV_TAG."
fi
