#!/bin/bash

# Generate a structured CHANGELOG.md from git history since the last tag

# 1. Find the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
  echo "No tags found. Generating changelog from the beginning of history."
  RANGE="main"
else
  echo "Generating changelog since tag: $LAST_TAG"
  RANGE="$LAST_TAG..main"
fi

# 2. Get commits in the range
COMMITS=$(git log "$RANGE" --pretty=format:"%s")

# 3. Initialize categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# 4. Categorize commits
while IFS= read -r commit; do
  if [[ "$commit" =~ (Added|feat|new) ]]; then
    ADDED+="- $commit\n"
  elif [[ "$commit" =~ (Fixed|fix|bug) ]]; then
    FIXED+="- $commit\n"
  elif [[ "$commit" =~ (Changed|update|refactor) ]]; then
    CHANGED+="- $commit\n"
  elif [[ "$commit" =~ (Removed|deprecate) ]]; then
    REMOVED+="- $commit\n"
  else
    CHANGED+="- $commit\n"
  fi
done <<< "$COMMITS"

# 5. Write to CHANGELOG.md
{
  echo "# Changelog"
  echo ""
  echo "## Latest Changes"
  echo ""
  
  if [ -n "$ADDED" ]; then
    echo "### 🚀 Added"
    echo -e "$ADDED"
    echo ""
  fi
  
  if [ -n "$FIXED" ]; then
    echo "### 🐛 Fixed"
    echo -e "$FIXED"
    echo ""
  fi
  
  if [ -n "$CHANGED" ]; then
    echo "### 🛠 Changed"
    echo -e "$CHANGED"
    echo ""
  fi
  
  if [ -n "$REMOVED" ]; then
    echo "### 🗑 Removed"
    echo -e "$REMOVED"
    echo ""
  fi
} > CHANGELOG.md

echo "CHANGELOG.md generated successfully."
