#!/bin/bash

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"%s")
else
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s")
fi

ADDED=$(echo "$COMMITS" | grep -iE '^(add|feat|added)' | sed -E 's/^[a-zA-Z]+(\([^)]+\))?: //i')
FIXED=$(echo "$COMMITS" | grep -iE '^(fix|fixed|bug)' | sed -E 's/^[a-zA-Z]+(\([^)]+\))?: //i')
CHANGED=$(echo "$COMMITS" | grep -iE '^(change|changed|update|updated|refactor)' | sed -E 's/^[a-zA-Z]+(\([^)]+\))?: //i')
REMOVED=$(echo "$COMMITS" | grep -iE '^(remove|removed|delete|deleted|drop)' | sed -E 's/^[a-zA-Z]+(\([^)]+\))?: //i')

echo "# CHANGELOG" > CHANGELOG.md
echo "" >> CHANGELOG.md

if [ -n "$ADDED" ]; then
    echo "## Added" >> CHANGELOG.md
    echo "$ADDED" | while read -r line; do
        if [ -n "$line" ]; then echo "- $line" >> CHANGELOG.md; fi
    done
    echo "" >> CHANGELOG.md
fi

if [ -n "$FIXED" ]; then
    echo "## Fixed" >> CHANGELOG.md
    echo "$FIXED" | while read -r line; do
        if [ -n "$line" ]; then echo "- $line" >> CHANGELOG.md; fi
    done
    echo "" >> CHANGELOG.md
fi

if [ -n "$CHANGED" ]; then
    echo "## Changed" >> CHANGELOG.md
    echo "$CHANGED" | while read -r line; do
        if [ -n "$line" ]; then echo "- $line" >> CHANGELOG.md; fi
    done
    echo "" >> CHANGELOG.md
fi

if [ -n "$REMOVED" ]; then
    echo "## Removed" >> CHANGELOG.md
    echo "$REMOVED" | while read -r line; do
        if [ -n "$line" ]; then echo "- $line" >> CHANGELOG.md; fi
    done
    echo "" >> CHANGELOG.md
fi

echo "CHANGELOG.md generated successfully."
