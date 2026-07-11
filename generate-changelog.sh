#!/usr/bin/env bash
#
# generate-changelog.sh
# Automatically generates a structured CHANGELOG.md from git history.
# Fetches commits since the last git tag and auto-categorizes them.
#
# Usage: bash generate-changelog.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the last git tag
get_last_tag() {
    git describe --tags --abbrev=0 2>/dev/null || echo ""
}

# Get commits since the last tag (or all commits if no tag)
get_commits_since_tag() {
    local tag="$1"
    if [ -n "$tag" ]; then
        git log "${tag}..HEAD" --pretty=format:"%s" --no-merges
    else
        git log --pretty=format:"%s" --no-merges
    fi
}

# Categorize a single commit message
categorize_commit() {
    local msg="$1"
    local lower_msg
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

    # Check for conventional commit prefixes or keywords
    if echo "$lower_msg" | grep -qE '^(feat|add|create|introduce|implement)'; then
        echo "added"
    elif echo "$lower_msg" | grep -qE '^(fix|bugfix|hotfix|repair|resolve|patch)'; then
        echo "fixed"
    elif echo "$lower_msg" | grep -qE '^(remove|delete|drop|revert|deprecate)'; then
        echo "removed"
    elif echo "$lower_msg" | grep -qE '^(update|change|modify|refactor|improve|enhance|upgrade|rework)'; then
        echo "changed"
    else
        # Fallback: check for keywords in the message
        if echo "$lower_msg" | grep -qE '\b(add|added|adding|new|feature|support)\b'; then
            echo "added"
        elif echo "$lower_msg" | grep -qE '\b(fix|fixed|fixing|bug|issue|resolve|patch|correct)\b'; then
            echo "fixed"
        elif echo "$lower_msg" | grep -qE '\b(remove|removed|removing|delete|deleted|drop|revert)\b'; then
            echo "removed"
        elif echo "$lower_msg" | grep -qE '\b(update|updated|updating|change|changed|modify|modified|refactor|improve|improved|enhance|enhanced|upgrade|upgraded|rework)\b'; then
            echo "changed"
        else
            echo "changed"  # Default category
        fi
    fi
}

# Main function
main() {
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}Error: Not a git repository.${NC}" >&2
        exit 1
    fi

    local last_tag
    last_tag=$(get_last_tag)

    if [ -n "$last_tag" ]; then
        echo -e "${YELLOW}Generating changelog since tag: $last_tag${NC}"
    else
        echo -e "${YELLOW}No tags found. Generating changelog from all commits.${NC}"
    fi

    # Get commits
    local commits
    commits=$(get_commits_since_tag "$last_tag")

    if [ -z "$commits" ]; then
        echo -e "${YELLOW}No commits found since last tag.${NC}"
        exit 0
    fi

    # Generate CHANGELOG.md
    {
        echo "# Changelog"
        echo ""
        if [ -n "$last_tag" ]; then
            echo "## Unreleased (since $last_tag)"
        else
            echo "## Unreleased"
        fi
        echo ""

        # Process and categorize commits
        echo "$commits" | while IFS= read -r commit; do
            [ -z "$commit" ] && continue
            categorize_commit "$commit"
        done | sort | uniq -c | sort -rn | while read -r count category; do
            echo "- $category: $count commit(s)"
        done

        echo ""
        echo "*Generated automatically by generate-changelog.sh*"
    } > CHANGELOG.md

    echo -e "${GREEN}CHANGELOG.md generated successfully!${NC}"
}

main "$@"