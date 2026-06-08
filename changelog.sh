#!/bin/bash

# Fetch the last tag, or get the first commit if no tags exist
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
  # No tags found, get all commits
  COMMITS=$(git log --pretty=format:"%s")
else
  # Get commits since the last tag
  COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s")
fi

echo "# CHANGELOG"
echo ""

# Output categories
for category in "Added" "Fixed" "Changed" "Removed"; do
  echo "## $category"
  
  # Case-insensitive grep for conventional commit prefixes or keywords
  cat <<EOF | grep -iE "^($category|feat|fix|refactor|remove)" <<< "$COMMITS" | while read -r line; do
    echo "- $line"
  done | grep -v "^$" || echo "*(None)*"
  
  echo ""
done
