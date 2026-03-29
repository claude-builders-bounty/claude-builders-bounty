#!/bin/bash
# Automatically generates a structured CHANGELOG.md from git history

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    # Fallback to all commits if no tags exist
    LOG_CMD="git log --pretty=format:\"- %h %s\" --no-merges"
else
    LOG_CMD="git log ${LAST_TAG}..HEAD --pretty=format:\"- %h %s\" --no-merges"
fi

COMMITS=$(eval $LOG_CMD)

if [ -z "$COMMITS" ]; then
    echo "No commits found to generate a changelog."
    exit 0
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# Categorize commits based on keywords
while IFS= read -r line; do
    if echo "$line" | grep -iE '\- [a-f0-9]+ (feat|add|new|create)' > /dev/null; then
        ADDED="${ADDED}${line}\n"
    elif echo "$line" | grep -iE '\- [a-f0-9]+ (fix|bug|patch)' > /dev/null; then
        FIXED="${FIXED}${line}\n"
    elif echo "$line" | grep -iE '\- [a-f0-9]+ (remove|delete|drop|deprecate)' > /dev/null; then
        REMOVED="${REMOVED}${line}\n"
    else
        # Default to Changed for refactors, chores, docs
        CHANGED="${CHANGED}${line}\n"
    fi
done <<< "$COMMITS"

OUTPUT="# Changelog\n\n## [Latest] - $(date +%Y-%m-%d)\n"

if [ -n "$ADDED" ]; then OUTPUT+="\n### Added\n${ADDED}"; fi
if [ -n "$FIXED" ]; then OUTPUT+="\n### Fixed\n${FIXED}"; fi
if [ -n "$CHANGED" ]; then OUTPUT+="\n### Changed\n${CHANGED}"; fi
if [ -n "$REMOVED" ]; then OUTPUT+="\n### Removed\n${REMOVED}"; fi

printf "%b\n" "$OUTPUT" > CHANGELOG.md
echo "CHANGELOG.md successfully generated."

