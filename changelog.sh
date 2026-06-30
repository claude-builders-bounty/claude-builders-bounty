#!/bin/bash
set -e

# Get the last tag, or fallback to first commit
last_tag=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

echo "# CHANGELOG" > CHANGELOG.md
echo "" >> CHANGELOG.md

if git describe --tags --abbrev=0 &>/dev/null; then
    echo "Changes since tag: $last_tag" >> CHANGELOG.md
else
    echo "All changes" >> CHANGELOG.md
fi
echo "" >> CHANGELOG.md

# Fetch commits
commits=$(git log ${last_tag}..HEAD --oneline --no-merges)

if [ -z "$commits" ]; then
    echo "No changes found." >> CHANGELOG.md
    exit 0
fi

# Categorize
declare -a added fixed changed removed other

while IFS= read -r line; do
    hash=$(echo "$line" | awk '{print $1}')
    msg=$(echo "$line" | cut -d' ' -f2-)
    
    # Simple regex matching on commit message for categories
    if echo "$msg" | grep -iqE '^(feat|add|added|create|new)\b'; then
        added+=("- $msg ($hash)")
    elif echo "$msg" | grep -iqE '^(fix|bug|fixed|hotfix)\b'; then
        fixed+=("- $msg ($hash)")
    elif echo "$msg" | grep -iqE '^(remove|delete|removed|drop|del)\b'; then
        removed+=("- $msg ($hash)")
    elif echo "$msg" | grep -iqE '^(change|update|changed|refactor|style|chore|docs|test)\b'; then
        changed+=("- $msg ($hash)")
    else
        other+=("- $msg ($hash)")
    fi
done <<< "$commits"

# Output categories
if [ ${#added[@]} -gt 0 ]; then
    echo "## Added" >> CHANGELOG.md
    printf "%s\n" "${added[@]}" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

if [ ${#fixed[@]} -gt 0 ]; then
    echo "## Fixed" >> CHANGELOG.md
    printf "%s\n" "${fixed[@]}" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

if [ ${#changed[@]} -gt 0 ]; then
    echo "## Changed" >> CHANGELOG.md
    printf "%s\n" "${changed[@]}" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

if [ ${#removed[@]} -gt 0 ]; then
    echo "## Removed" >> CHANGELOG.md
    printf "%s\n" "${removed[@]}" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

if [ ${#other[@]} -gt 0 ]; then
    echo "## Other" >> CHANGELOG.md
    printf "%s\n" "${other[@]}" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
fi

echo "CHANGELOG.md generated successfully!"
