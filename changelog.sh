#!/bin/bash
# CHANGELOG Generator - Bash version
# Automatically generate structured CHANGELOG.md from git history

set -e

REPO_PATH="${1:-.}"
cd "$REPO_PATH" || exit 1

if [ ! -d ".git" ]; then
    echo "Error: Not a git repository" >&2
    exit 1
fi

# Get the last tag
LAST_TAG=$(git tag -l --sort=-version:refname | head -1)

# Determine commit range
if [ -z "$LAST_TAG" ]; then
    COMMIT_RANGE="HEAD"
else
    COMMIT_RANGE="$LAST_TAG..HEAD"
fi

# Initialize changelog
CHANGELOG="# CHANGELOG\n\n## [Unreleased]\n\n"

# Categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# Process commits
while IFS='|' read -r HASH SUBJECT BODY AUTHOR DATE; do
    # Skip empty lines
    [ -z "$SUBJECT" ] && continue
    
    # Categorize commit
    TEXT="${SUBJECT} ${BODY}"
    CATEGORY="Changed"
    
    if echo "$TEXT" | grep -qi "fix:\|fixed\|bug fix\|resolve\|closes #\|fixes #"; then
        CATEGORY="Fixed"
    elif echo "$TEXT" | grep -qi "feat:\|feature\|add:\|added\|new"; then
        CATEGORY="Added"
    elif echo "$TEXT" | grep -qi "remove:\|removed\|delete:\|deleted\|deprecat"; then
        CATEGORY="Removed"
    fi
    
    # Clean up subject
    SUBJECT=$(echo "$SUBJECT" | sed 's/^(feat|fix|docs|style|refactor|perf|test|chore):\s*//')
    
    # Format commit message
    COMMIT_MSG="- ${SUBJECT} ([$HASH](https://github.com/claude-builders-bounty/claude-builders-bounty/commit/$HASH ))"
    
    # Add to appropriate category
    case "$CATEGORY" in
        Added)
            ADDED="${ADDED}${COMMIT_MSG}\n"
            ;;
        Fixed)
            FIXED="${FIXED}${COMMIT_MSG}\n"
            ;;
        Removed)
            REMOVED="${REMOVED}${COMMIT_MSG}\n"
            ;;
        *)
            CHANGED="${CHANGED}${COMMIT_MSG}\n"
            ;;
    esac
done < <(git log "$COMMIT_RANGE" --pretty=format:"%h|%s|%b|%an|%ai")

# Build changelog sections
if [ -n "$ADDED" ]; then
    CHANGELOG="${CHANGELOG}### Added\n\n${ADDED}\n"
fi

if [ -n "$FIXED" ]; then
    CHANGELOG="${CHANGELOG}### Fixed\n\n${FIXED}\n"
fi

if [ -n "$CHANGED" ]; then
    CHANGELOG="${CHANGELOG}### Changed\n\n${CHANGED}\n"
fi

if [ -n "$REMOVED" ]; then
    CHANGELOG="${CHANGELOG}### Removed\n\n${REMOVED}\n"
fi

# Add historical tags
if [ -n "$LAST_TAG" ]; then
    CHANGELOG="${CHANGELOG}\n## Historical Releases\n\n"
    git tag -l --sort=-version:refname | head -5 | while read -r TAG; do
        CHANGELOG="${CHANGELOG}- [$TAG](https://github.com/claude-builders-bounty/claude-builders-bounty/releases/tag/$TAG )\n"
    done
fi

# Write to file
echo -e "$CHANGELOG" > CHANGELOG.md
echo "✅ CHANGELOG.md generated successfully"
echo ""
echo "Preview:"
head -20 CHANGELOG.md
