#!/usr/bin/env bash
set -euo pipefail

# changelog.sh — Generate a structured CHANGELOG.md from git history.
# Fetches commits since the last git tag, auto-categorizes them, and
# outputs a properly formatted CHANGELOG.md.

CHANGELOG_FILE="CHANGELOG.md"
REPO_URL=$(git config --get remote.origin.url 2>/dev/null || echo "")

# Determine the range of commits
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
    VERSION=$(echo "$LAST_TAG" | sed 's/^v//')
else
    RANGE=""
    VERSION="0.1.0"
fi

DATE=$(date +%Y-%m-%d)

# Collect commits
if [ -n "$RANGE" ]; then
    COMMITS=$(git log "$RANGE" --pretty=format:"%H%x09%s%x09%an" --no-merges)
else
    COMMITS=$(git log --pretty=format:"%H%x09%s%x09%an" --no-merges -50)
fi

# Temporary files for categories
TMP_ADDED=$(mktemp)
TMP_FIXED=$(mktemp)
TMP_CHANGED=$(mktemp)
TMP_REMOVED=$(mktemp)
TMP_DOCS=$(mktemp)
TMP_CHORE=$(mktemp)

cleanup() { rm -f "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED" "$TMP_DOCS" "$TMP_CHORE"; }
trap cleanup EXIT

while IFS=$'\t' read -r hash subject author; do
    lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

    # Extract scope from conventional commit format (e.g. feat(auth): ...)
    scope=""
    if echo "$subject" | grep -qE '^[a-z]+\([^)]+\):'; then
        scope=$(echo "$subject" | sed -E 's/^[a-z]+\(([^)]+)\):.*/\1/')
    fi

    # Clean subject: strip conventional commit prefix
    clean_subject=$(echo "$subject" | sed -E 's/^[a-z]+(\([^)]+\))?:[[:space:]]*//')

    # Build commit link if repo URL is available
    if [ -n "$REPO_URL" ]; then
        if echo "$REPO_URL" | grep -q "github.com"; then
            COMMIT_LINK=$(echo "$REPO_URL" | sed 's/\.git$//')"/commit/${hash:0:7}"
            entry="- ${clean_subject} ([${hash:0:7}](${COMMIT_LINK}))"
        else
            entry="- ${clean_subject} (${hash:0:7})"
        fi
    else
        entry="- ${clean_subject} (${hash:0:7})"
    fi

    # Categorize
    if echo "$lower" | grep -qE '^(feat|add|feature|create|implement|introduce|support)'; then
        echo "$entry" >> "$TMP_ADDED"
    elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|repair|hotfix)'; then
        echo "$entry" >> "$TMP_FIXED"
    elif echo "$lower" | grep -qE '^(refactor|change|update|modify|move|rename|improve|enhance|migrate|upgrade|bump)'; then
        echo "$entry" >> "$TMP_CHANGED"
    elif echo "$lower" | grep -qE '^(remove|delete|drop|strip|deprecate|retire)'; then
        echo "$entry" >> "$TMP_REMOVED"
    elif echo "$lower" | grep -qE '^(doc|docs|readme|changelog|comment|typo|spell)'; then
        echo "$entry" >> "$TMP_DOCS"
    else
        echo "$entry" >> "$TMP_CHORE"
    fi
done <<< "$COMMITS"

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [${VERSION}] - ${DATE}"
    echo ""

    if [ -s "$TMP_ADDED" ]; then
        echo "### Added"
        echo ""
        cat "$TMP_ADDED"
        echo ""
    fi

    if [ -s "$TMP_CHANGED" ]; then
        echo "### Changed"
        echo ""
        cat "$TMP_CHANGED"
        echo ""
    fi

    if [ -s "$TMP_FIXED" ]; then
        echo "### Fixed"
        echo ""
        cat "$TMP_FIXED"
        echo ""
    fi

    if [ -s "$TMP_REMOVED" ]; then
        echo "### Removed"
        echo ""
        cat "$TMP_REMOVED"
        echo ""
    fi

    if [ -s "$TMP_DOCS" ]; then
        echo "### Documentation"
        echo ""
        cat "$TMP_DOCS"
        echo ""
    fi

    if [ -s "$TMP_CHORE" ]; then
        echo "### Maintenance"
        echo ""
        cat "$TMP_CHORE"
        echo ""
    fi
} > "$CHANGELOG_FILE"

echo "Generated ${CHANGELOG_FILE}"
echo "  Added:      $(wc -l < "$TMP_ADDED" | tr -d ' ')"
echo "  Changed:    $(wc -l < "$TMP_CHANGED" | tr -d ' ')"
echo "  Fixed:      $(wc -l < "$TMP_FIXED" | tr -d ' ')"
echo "  Removed:    $(wc -l < "$TMP_REMOVED" | tr -d ' ')"
echo "  Docs:       $(wc -l < "$TMP_DOCS" | tr -d ' ')"
echo "  Maintenance: $(wc -l < "$TMP_CHORE" | tr -d ' ')"
