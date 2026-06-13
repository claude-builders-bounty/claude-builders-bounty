#!/usr/bin/env bash
set -e

# Output file
OUT_FILE="CHANGELOG.md"

# Find the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo "No tags found, generating changelog from all commits"
    COMMITS=$(git log --no-merges --pretty=format:"%s")
else
    echo "Generating changelog for commits since $LAST_TAG"
    COMMITS=$(git log $LAST_TAG..HEAD --no-merges --pretty=format:"%s")
fi

echo "# Changelog" > "$OUT_FILE"
echo "" >> "$OUT_FILE"
echo "## [Unreleased] - $(date +%Y-%m-%d)" >> "$OUT_FILE"
echo "" >> "$OUT_FILE"

# Arrays for each category
declare -a ADDED
declare -a FIXED
declare -a CHANGED
declare -a REMOVED

while IFS= read -r msg; do
    # Skip empty lines
    if [ -z "$msg" ]; then continue; fi
    
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lower_msg" =~ ^(feat|add|feature): ]] || [[ "$lower_msg" =~ ^added ]]; then
        ADDED+=("- $msg")
    elif [[ "$lower_msg" =~ ^(fix|bug|hotfix): ]] || [[ "$lower_msg" =~ ^fixed ]]; then
        FIXED+=("- $msg")
    elif [[ "$lower_msg" =~ ^(remove|rm|drop|delete): ]] || [[ "$lower_msg" =~ ^removed ]]; then
        REMOVED+=("- $msg")
    else
        CHANGED+=("- $msg")
    fi
done <<< "$COMMITS"

if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added" >> "$OUT_FILE"
    printf "%s\n" "${ADDED[@]}" >> "$OUT_FILE"
    echo "" >> "$OUT_FILE"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed" >> "$OUT_FILE"
    printf "%s\n" "${FIXED[@]}" >> "$OUT_FILE"
    echo "" >> "$OUT_FILE"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed" >> "$OUT_FILE"
    printf "%s\n" "${CHANGED[@]}" >> "$OUT_FILE"
    echo "" >> "$OUT_FILE"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed" >> "$OUT_FILE"
    printf "%s\n" "${REMOVED[@]}" >> "$OUT_FILE"
    echo "" >> "$OUT_FILE"
fi

echo "Successfully generated $OUT_FILE"
