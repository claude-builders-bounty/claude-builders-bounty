#!/bin/bash
# Generate a structured CHANGELOG.md from git history

# Find the last tag; if none exists, use the first commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"%s" 2>/dev/null)
else
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s" 2>/dev/null)
fi

# Arrays to hold categorized commits
declare -a added fixed changed removed other

while IFS= read -r msg; do
    if [[ -z "$msg" ]]; then continue; fi
    # Simple regex matching for conventional commit prefixes or keywords
    if echo "$msg" | grep -qiE "^(add|feat|added)"; then
        added+=("- $msg")
    elif echo "$msg" | grep -qiE "^(fix|fixed|bug|hotfix)"; then
        fixed+=("- $msg")
    elif echo "$msg" | grep -qiE "^(remove|delete|removed|drop)"; then
        removed+=("- $msg")
    elif echo "$msg" | grep -qiE "^(change|update|changed|refactor|chore|docs|style|test|perf)"; then
        changed+=("- $msg")
    else
        other+=("- $msg")
    fi
done <<< "$COMMITS"

# Write to CHANGELOG.md
echo "# CHANGELOG" > CHANGELOG.md

if [ ${#added[@]} -gt 0 ]; then
    echo -e "\n## Added" >> CHANGELOG.md
    printf "%s\n" "${added[@]}" >> CHANGELOG.md
fi
if [ ${#fixed[@]} -gt 0 ]; then
    echo -e "\n## Fixed" >> CHANGELOG.md
    printf "%s\n" "${fixed[@]}" >> CHANGELOG.md
fi
if [ ${#changed[@]} -gt 0 ]; then
    echo -e "\n## Changed" >> CHANGELOG.md
    printf "%s\n" "${changed[@]}" >> CHANGELOG.md
fi
if [ ${#removed[@]} -gt 0 ]; then
    echo -e "\n## Removed" >> CHANGELOG.md
    printf "%s\n" "${removed[@]}" >> CHANGELOG.md
fi
if [ ${#other[@]} -gt 0 ]; then
    echo -e "\n## Other" >> CHANGELOG.md
    printf "%s\n" "${other[@]}" >> CHANGELOG.md
fi

echo "CHANGELOG.md successfully generated."
