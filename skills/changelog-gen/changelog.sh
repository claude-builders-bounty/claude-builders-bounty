#!/bin/bash
# Generate structured CHANGELOG.md from git history

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"%s")
else
    COMMITS=$(git log $LAST_TAG..HEAD --pretty=format:"%s")
fi

echo "## CHANGELOG"
echo "### Added"
echo "$COMMITS" | grep -iE "^(add|feat|new)" | sed 's/^/- /'
echo ""
echo "### Fixed"
echo "$COMMITS" | grep -iE "^(fix|bug|patch)" | sed 's/^/- /'
echo ""
echo "### Changed"
echo "$COMMITS" | grep -iE "^(change|update|refactor)" | sed 's/^/- /'
echo ""
echo "### Removed"
echo "$COMMITS" | grep -iE "^(remove|del)" | sed 's/^/- /'
