#!/usr/bin/env bash
# generate-changelog.sh — Generate structured CHANGELOG from git history
# Usage: ./generate-changelog.sh [output_file]

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
REPO_NAME=$(basename -s .git "$REPO_URL" 2>/dev/null || echo "$(basename "$PWD")")

# Get the last tag, or use empty if no tags
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
    COMMIT_RANGE="${LAST_TAG}..HEAD"
    echo "Generating changelog for commits since $LAST_TAG..."
else
    COMMIT_RANGE="HEAD"
    echo "No tags found. Generating changelog for all commits..."
fi

# Get commits with subjects
COMMITS=$(git log "$COMMIT_RANGE" --pretty=format:"%s" --no-merges 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
    echo "No commits found in range."
    exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    
    lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    
    if echo "$lower" | grep -qE '^(feat|add|introduce|implement|new)'; then
        ADDED="${ADDED}- ${line}"$'\n'
    elif echo "$lower" | grep -qE '^(fix|bug|repair|correct|resolve|hotfix)'; then
        FIXED="${FIXED}- ${line}"$'\n'
    elif echo "$lower" | grep -qE '^(change|update|modify|refactor|improve|enhance|upgrade|deprecate)'; then
        CHANGED="${CHANGED}- ${line}"$'\n'
    elif echo "$lower" | grep -qE '^(remove|delete|drop|clean|cleanup|revert)'; then
        REMOVED="${REMOVED}- ${line}"$'\n'
    else
        OTHER="${OTHER}- ${line}"$'\n'
    fi
done <<< "$COMMITS"

# Generate the CHANGELOG
DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "unreleased")

cat > "$OUTPUT" << EOF
# Changelog

All notable changes to this project will be documented in this file.

## [$VERSION] - $DATE

EOF

append_section() {
    local title="$1"
    local content="$2"
    if [ -n "$content" ]; then
        echo "### $title" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
        echo "$content" >> "$OUTPUT"
    fi
}

append_section "Added" "$ADDED"
append_section "Fixed" "$FIXED"
append_section "Changed" "$CHANGED"
append_section "Removed" "$REMOVED"
append_section "Other" "$OTHER"

echo "✅ Changelog written to $OUTPUT"
