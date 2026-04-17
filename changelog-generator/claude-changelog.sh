#!/bin/bash
# claude-changelog.sh - Generate structured CHANGELOG from git history
# Usage: ./claude-changelog.sh [from-tag] [to-tag]

set -e

FROM_TAG="${1:-}"
TO_TAG="${2:-HEAD}"
REPO_NAME="${REPO_NAME:-$(basename $(git rev-parse --show-toplevel))}"

# Get commits between tags or from beginning
if [ -n "$FROM_TAG" ]; then
    COMMITS=$(git log --format="%h %s" "$FROM_TAG..$TO_TAG" 2>/dev/null || git log --format="%h %s" -100)
else
    COMMITS=$(git log --format="%h %s" -100)
fi

# Generate changelog sections
echo "# Changelog - $REPO_NAME"
echo ""
echo "## Unreleased"
echo ""

# Categorize commits
echo "### Features"
git log --format="  - %s" --grep="feat" --grep="feature" --all-match $FROM_TAG..$TO_TAG 2>/dev/null || echo "  (none)"
echo ""

echo "### Bug Fixes"
git log --format="  - %s" --grep="fix" --grep="bug" --all-match $FROM_TAG..$TO_TAG 2>/dev/null || echo "  (none)"
echo ""

echo "### Other Changes"
git log --format="  - %s" --grep="^[^f]" --all-match --invert-grep $FROM_TAG..$TO_TAG 2>/dev/null || echo "  (none)"

# If no tags found, show all recent commits
if [ -z "$FROM_TAG" ]; then
    echo ""
    echo "---"
    echo "Full history (last 50 commits):"
    git log --format="  - %h %s" -50
fi
