#!/bin/bash
# changelog.sh - Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file] [repo_directory]
# Default output: CHANGELOG.md

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_DIR="${2:-.}"

cd "$REPO_DIR"

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository."
    exit 1
fi

# Get the last tag (fall back to first commit if no tags exist)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

echo "Generating CHANGELOG since: $LAST_TAG"

# Get commits since last tag
GIT_LOG=$(git log "$LAST_TAG..HEAD" --pretty=format:"%h|||%s|||%an|||%ad" --date=short 2>/dev/null || \
          git log --pretty=format:"%h|||%s|||%an|||%ad" --date=short 2>/dev/null)

if [ -z "$GIT_LOG" ]; then
    echo "No commits found since $LAST_TAG. Nothing to generate."
    exit 0
fi

ADDED=""; FIXED=""; CHANGED=""; REMOVED=""; OTHER=""

while IFS='|||' read -r HASH TITLE AUTHOR DATE; do
    [ -z "$TITLE" ] && continue
    
    LOWERCASE=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]')
    
    if echo "$LOWERCASE" | grep -qE '^(feat|feature|add|implement|create|introduce)'; then
        ADDED="$ADDED
- $TITLE (#$HASH) by @$AUTHOR"
    elif echo "$LOWERCASE" | grep -qE '^(fix|bugfix|hotfix|patch|correct|resolve)'; then
        FIXED="$FIXED
- $TITLE (#$HASH) by @$AUTHOR"
    elif echo "$LOWERCASE" | grep -qE '^(change|update|refactor|improve|migrate|perf|optimize|style)'; then
        CHANGED="$CHANGED
- $TITLE (#$HASH) by @$AUTHOR"
    elif echo "$LOWERCASE" | grep -qE '^(remove|delete|deprecate|drop)'; then
        REMOVED="$REMOVED
- $TITLE (#$HASH) by @$AUTHOR"
    else
        OTHER="$OTHER
- $TITLE (#$HASH) by @$AUTHOR"
    fi
done <<< "$GIT_LOG"

{
    echo "# Changelog"
    echo ""
    echo "## [Unreleased] - $(date +%Y-%m-%d)"
    echo ""
    [ -n "$ADDED" ] && { echo "### Added"; echo "$ADDED"; echo ""; }
    [ -n "$FIXED" ] && { echo "### Fixed"; echo "$FIXED"; echo ""; }
    [ -n "$CHANGED" ] && { echo "### Changed"; echo "$CHANGED"; echo ""; }
    [ -n "$REMOVED" ] && { echo "### Removed"; echo "$REMOVED"; echo ""; }
    [ -n "$OTHER" ] && { echo "### Other"; echo "$OTHER"; echo ""; }
} > "$OUTPUT"

echo "✅ CHANGELOG generated at: $OUTPUT"