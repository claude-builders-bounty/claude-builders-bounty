#!/bin/bash

# Find the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    # If no tag exists, get all commits
    COMMITS=$(git log --pretty=format:"%s")
    echo "No tags found. Generating changelog from all commits."
else
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s")
    echo "Generating changelog since tag: $LAST_TAG"
fi

# Categorize commits
ADDED=$(echo "$COMMITS" | grep -iE "^(add|feat|new)\b" | sed 's/^[a-zA-Z]*:\{0,1\} /- /I' || true)
FIXED=$(echo "$COMMITS" | grep -iE "^(fix|bug)\b" | sed 's/^[a-zA-Z]*:\{0,1\} /- /I' || true)
CHANGED=$(echo "$COMMITS" | grep -iE "^(change|update|refactor|modify)\b" | sed 's/^[a-zA-Z]*:\{0,1\} /- /I' || true)
REMOVED=$(echo "$COMMITS" | grep -iE "^(remove|delete|drop)\b" | sed 's/^[a-zA-Z]*:\{0,1\} /- /I' || true)
OTHER=$(echo "$COMMITS" | grep -ivE "^(add|feat|new|fix|bug|change|update|refactor|modify|remove|delete|drop)\b" | sed 's/^/- /' || true)

# Build CHANGELOG.md
cat <<EOF > CHANGELOG.md
# Changelog

*Auto-generated changelog for recent commits.*

EOF

if [ -n "$ADDED" ]; then
    echo "## Added" >> CHANGELOG.md
    echo "$ADDED" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

if [ -n "$FIXED" ]; then
    echo "## Fixed" >> CHANGELOG.md
    echo "$FIXED" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

if [ -n "$CHANGED" ]; then
    echo "## Changed" >> CHANGELOG.md
    echo "$CHANGED" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

if [ -n "$REMOVED" ]; then
    echo "## Removed" >> CHANGELOG.md
    echo "$REMOVED" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

if [ -n "$OTHER" ]; then
    echo "## Other" >> CHANGELOG.md
    echo "$OTHER" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

echo "CHANGELOG.md generated successfully!"
