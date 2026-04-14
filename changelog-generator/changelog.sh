#!/bin/bash

# Simple script to generate a structured CHANGELOG.md from git history since the last tag.

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
COMMITS=$(git log $LAST_TAG..HEAD --pretty=format:"%s")

echo "# Changelog" > CHANGELOG.md
echo "" >> CHANGELOG.md
echo "## Unreleased" >> CHANGELOG.md

# Helper function to extract and format commits based on keywords
extract_commits() {
  local category=$1
  shift
  local keywords=("$@")
  
  local category_commits=""
  for keyword in "${keywords[@]}"; do
    # Case-insensitive grep for keywords like "add", "added", "feat", etc.
    matches=$(echo "$COMMITS" | grep -iE "^$keyword" | sed -e "s/^$keyword[s]*[ :]*//I" -e "s/^/- /")
    if [ -n "$matches" ]; then
      category_commits="$category_commits\n$matches"
    fi
  done
  
  if [ -n "$category_commits" ] && [ "$category_commits" != "\n" ]; then
    echo "" >> CHANGELOG.md
    echo "### $category" >> CHANGELOG.md
    echo -e "$category_commits" | grep -v "^$" >> CHANGELOG.md
  fi
}

extract_commits "Added" "add" "added" "feat" "feature"
extract_commits "Fixed" "fix" "fixed" "bug" "bugfix"
extract_commits "Changed" "change" "changed" "update" "updated" "refactor" "modify" "modified"
extract_commits "Removed" "remove" "removed" "delete" "deleted" "drop" "dropped"

echo "CHANGELOG.md generated successfully!"
