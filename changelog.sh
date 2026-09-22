#!/bin/bash

# changelog.sh
# Fetches commits since the last git tag and auto-categorizes them into a CHANGELOG.md

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -z "$LAST_TAG" ]; then
    LAST_TAG=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
fi

if [ -z "$LAST_TAG" ]; then
    echo "No commits found."
    exit 0
fi

echo "Generating changelog since: ${LAST_TAG:-Beginning}"

if [ "$LAST_TAG" == "$(git rev-list --max-parents=0 HEAD 2>/dev/null)" ]; then
    COMMITS=$(git log --pretty=format:"%s (%h)")
else
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s (%h)")
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r commit; do
    if [[ -z "$commit" ]]; then continue; fi

    # Lowercase the commit message for easier matching
    LOWER_COMMIT=$(echo "$commit" | tr '[:upper:]' '[:lower:]')

    # Categorize based on keywords or conventional commit prefixes
    if echo "$LOWER_COMMIT" | grep -qE "^(feat|add|create|new|implement)(\(|:)"; then
        ADDED+="- $commit"$'\n'
    elif echo "$LOWER_COMMIT" | grep -qE "^(fix|bug|patch|resolve|repair)(\(|:)"; then
        FIXED+="- $commit"$'\n'
    elif echo "$LOWER_COMMIT" | grep -qE "^(remove|drop|delete|prune)(\(|:)"; then
        REMOVED+="- $commit"$'\n'
    else
        CHANGED+="- $commit"$'\n'
    fi
done <<< "$COMMITS"

OUTPUT="# CHANGELOG\n"

if [ -n "$ADDED" ]; then
    OUTPUT+="\n## Added\n$ADDED"
fi
if [ -n "$FIXED" ]; then
    OUTPUT+="\n## Fixed\n$FIXED"
fi
if [ -n "$CHANGED" ]; then
    OUTPUT+="\n## Changed\n$CHANGED"
fi
if [ -n "$REMOVED" ]; then
    OUTPUT+="\n## Removed\n$REMOVED"
fi

if [ -z "$ADDED" ] && [ -z "$FIXED" ] && [ -z "$CHANGED" ] && [ -z "$REMOVED" ]; then
    OUTPUT+="\nNo notable changes found."
fi

echo -e "$OUTPUT" > CHANGELOG.md
echo "CHANGELOG.md has been generated successfully."
