#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history since the last tag.
# Usage: ./changelog.sh [--output CHANGELOG.md]
set -euo pipefail

OUTPUT="${2:-CHANGELOG.md}"

# Get the last tag or the first commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
    # No tags yet, use the first commit
    LAST_TAG=$(git rev-list --max-parents=0 HEAD)
    echo "No tags found — using first commit as baseline"
else
    echo "Generating changelog since $LAST_TAG"
fi

# Get commits since last tag
COMMITS=$(git log "$LAST_TAG..HEAD" --pretty=format:"%s" --no-merges 2>/dev/null || git log --pretty=format:"%s" --no-merges)

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    # Skip merge commits and empty lines
    [[ "$line" =~ ^Merge ]] && continue
    
    if echo "$line" | grep -qiE '^(add|feat|new|create|implement|introduce)'; then
        ADDED+="  - $line"$'\n'
    elif echo "$line" | grep -qiE '^(fix|bug|patch|resolve|repair|hotfix)'; then
        FIXED+="  - $line"$'\n'
    elif echo "$line" | grep -qiE '^(remove|drop|delete|deprecate|retire)'; then
        REMOVED+="  - $line"$'\n'
    else
        CHANGED+="  - $line"$'\n'
    fi
done <<< "$COMMITS"

# Get today's date
DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "unreleased")

# Generate changelog
cat > "$OUTPUT" << CHANGELOG
# Changelog

## [$VERSION] - $DATE

### Added
${ADDED:-  - _None_}

### Fixed
${FIXED:-  - _None_}

### Changed
${CHANGED:-  - _None_}

### Removed
${REMOVED:-  - _None_}
CHANGELOG

echo "Changelog written to $OUTPUT"
echo ""
echo "Preview:"
head -30 "$OUTPUT"
