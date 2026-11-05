#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_DIR="${2:-$(git rev-parse --show-toplevel)}"

cd "$REPO_DIR"

# Find the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
else
    RANGE="HEAD"
    LAST_TAG="(no previous tags)"
fi

# Date and version
DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' || echo "0.1.0")

# Collect commits
COMMITS=$(git log --pretty=format:'%s' $RANGE 2>/dev/null || echo "")

# Categorize using arrays
added_list=(); fixed_list=(); changed_list=(); removed_list=()

while IFS= read -r line; do
    [ -z "$line" ] && continue
    lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    case "$lower" in
        feat:*|add:*|new:*|introduce:*)
            added_list+=("$line") ;;
        fix:*|bug:*|patch:*|correct:*)
            fixed_list+=("$line") ;;
        change:*|update:*|modify:*|refactor:*|improve:*|perf:*)
            changed_list+=("$line") ;;
        remove:*|delete:*|drop:*)
            removed_list+=("$line") ;;
        *)
            changed_list+=("$line") ;;
    esac
done <<< "$COMMITS"

# Generate output using printf
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [${VERSION}] - ${DATE}"
    echo ""
    
    echo "### Added"
    if [ ${#added_list[@]} -gt 0 ]; then
        printf '%s\n' "${added_list[@]/#/- }"
    else
        echo "- No new features"
    fi
    echo ""
    
    echo "### Fixed"
    if [ ${#fixed_list[@]} -gt 0 ]; then
        printf '%s\n' "${fixed_list[@]/#/- }"
    else
        echo "- No bug fixes"
    fi
    echo ""
    
    echo "### Changed"
    if [ ${#changed_list[@]} -gt 0 ]; then
        printf '%s\n' "${changed_list[@]/#/- }"
    else
        echo "- No changes"
    fi
    echo ""
    
    echo "### Removed"
    if [ ${#removed_list[@]} -gt 0 ]; then
        printf '%s\n' "${removed_list[@]/#/- }"
    else
        echo "- No removals"
    fi
} > "$OUTPUT"

echo "CHANGELOG.md generated: $OUTPUT"
echo "Version: $VERSION, Date: $DATE, Commits: $(echo "$COMMITS" | grep -c . || echo 0)"
