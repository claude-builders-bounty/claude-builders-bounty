#!/bin/bash
# Generate a structured CHANGELOG.md from git history

# Fetch the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
  # If no tag, get all commits
  COMMITS=$(git log --pretty=format:"%s|%h" --no-merges)
  TAG_LABEL="Initial Commit"
else
  COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s|%h" --no-merges)
  TAG_LABEL="$LAST_TAG"
fi

if [ -z "$COMMITS" ]; then
  echo "No commits found to generate changelog."
  exit 0
fi

echo "# CHANGELOG" > CHANGELOG.md
echo "" >> CHANGELOG.md
echo "## Changes since $TAG_LABEL" >> CHANGELOG.md
echo "" >> CHANGELOG.md

declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED

while IFS='|' read -r msg hash; do
  [ -z "$msg" ] && continue
  msg_lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
  if [[ "$msg_lower" == feat* || "$msg_lower" == add* ]]; then
    ADDED+=("- $msg (\`$hash\`)")
  elif [[ "$msg_lower" == fix* || "$msg_lower" == bug* ]]; then
    FIXED+=("- $msg (\`$hash\`)")
  elif [[ "$msg_lower" == remove* || "$msg_lower" == delete* ]]; then
    REMOVED+=("- $msg (\`$hash\`)")
  else
    CHANGED+=("- $msg (\`$hash\`)")
  fi
done <<< "$COMMITS"

if [ ${#ADDED[@]} -gt 0 ]; then
  echo "### 🚀 Added" >> CHANGELOG.md
  printf "%s\n" "${ADDED[@]}" >> CHANGELOG.md
  echo "" >> CHANGELOG.md
fi

if [ ${#FIXED[@]} -gt 0 ]; then
  echo "### 🐛 Fixed" >> CHANGELOG.md
  printf "%s\n" "${FIXED[@]}" >> CHANGELOG.md
  echo "" >> CHANGELOG.md
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
  echo "### 🔄 Changed" >> CHANGELOG.md
  printf "%s\n" "${CHANGED[@]}" >> CHANGELOG.md
  echo "" >> CHANGELOG.md
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
  echo "### 🗑️ Removed" >> CHANGELOG.md
  printf "%s\n" "${REMOVED[@]}" >> CHANGELOG.md
  echo "" >> CHANGELOG.md
fi

echo "CHANGELOG.md generated successfully!"
