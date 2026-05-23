#!/bin/bash

# changelog.sh
# Generates a structured CHANGELOG.md from git history since the last tag.
# Auto-categorizes into: Added / Fixed / Changed / Removed

echo "Generating CHANGELOG.md..."

# Find the latest tag. If no tags exist, use the first commit.
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -z "$LAST_TAG" ]; then
    LAST_TAG=$(git rev-list --max-parents=0 HEAD 2>/dev/null | tail -n 1)
    RANGE="HEAD"
    HEADER="## Commits (Initial release)"
else
    RANGE="$LAST_TAG..HEAD"
    HEADER="## Commits since $LAST_TAG"
fi

echo "# CHANGELOG" > CHANGELOG.md
echo "" >> CHANGELOG.md
echo "$HEADER" >> CHANGELOG.md
echo "" >> CHANGELOG.md

# Temporary files for categories
touch added.tmp fixed.tmp changed.tmp removed.tmp

# Get commits in the range
git log "$RANGE" --pretty=format:"%s" | while read -r msg; do
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    # Categorize based on keywords
    if [[ "$lower_msg" == *"add"* || "$lower_msg" == *"feat"* || "$lower_msg" == *"new"* ]]; then
        echo "- $msg" >> added.tmp
    elif [[ "$lower_msg" == *"fix"* || "$lower_msg" == *"bug"* || "$lower_msg" == *"patch"* || "$lower_msg" == *"resolve"* ]]; then
        echo "- $msg" >> fixed.tmp
    elif [[ "$lower_msg" == *"remov"* || "$lower_msg" == *"delet"* || "$lower_msg" == *"drop"* || "$lower_msg" == *"deprecat"* ]]; then
        echo "- $msg" >> removed.tmp
    else
        echo "- $msg" >> changed.tmp
    fi
done

# Assemble the final CHANGELOG
for cat in "Added:added.tmp" "Fixed:fixed.tmp" "Changed:changed.tmp" "Removed:removed.tmp"; do
    TITLE=${cat%%:*}
    FILE=${cat##*:}
    if [ -s "$FILE" ]; then
        echo "### $TITLE" >> CHANGELOG.md
        cat "$FILE" >> CHANGELOG.md
        echo "" >> CHANGELOG.md
    fi
    rm -f "$FILE"
done

echo "Successfully generated CHANGELOG.md!"
