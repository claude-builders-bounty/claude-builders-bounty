#!/bin/bash

# Find the latest git tag, if one exists
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

# Get commit messages
if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Using entire git history."
    COMMITS=$(git log --pretty=format:"%s")
else
    echo "Last tag found: $LAST_TAG"
    COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%s")
fi

# Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# Process commits
while IFS= read -r COMMIT; do
    if [[ "$COMMIT" =~ ^feat(\(.*\))?: ]]; then
        ADDED="${ADDED}- ${COMMIT#*: }\n"

    elif [[ "$COMMIT" =~ ^fix(\(.*\))?: ]]; then
        FIXED="${FIXED}- ${COMMIT#*: }\n"

    elif [[ "$COMMIT" =~ ^(refactor|chore)(\(.*\))?: ]]; then
        CHANGED="${CHANGED}- ${COMMIT#*: }\n"

    elif [[ "$COMMIT" =~ ^(remove|delete)(\(.*\))?: ]]; then
        REMOVED="${REMOVED}- ${COMMIT#*: }\n"
    fi
done <<< "$COMMITS"

# Generate changelog file
cat > CHANGELOG.md << EOF
# Changelog

## Added
$(echo -e "$ADDED")

## Fixed
$(echo -e "$FIXED")

## Changed
$(echo -e "$CHANGED")

## Removed
$(echo -e "$REMOVED")
EOF

echo "CHANGELOG.md generated successfully."
