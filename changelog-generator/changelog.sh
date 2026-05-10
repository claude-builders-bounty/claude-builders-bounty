#!/bin/bash
# A simple script to auto-generate a structured CHANGELOG.md from git history

# Get the last tag, or fallback to the first commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Fetching all commits."
    REVISION_RANGE="HEAD"
    LAST_TAG_MSG="Initial"
else
    echo "Found last tag: $LAST_TAG"
    REVISION_RANGE="$LAST_TAG..HEAD"
    LAST_TAG_MSG="$LAST_TAG"
fi

# Fetch commits in format "hash||subject"
COMMITS=$(git log $REVISION_RANGE --pretty=format:"%h||%s")

if [ -z "$COMMITS" ]; then
    echo "No new commits found since last tag."
    exit 0
fi

TMP_ADDED=$(mktemp)
TMP_FIXED=$(mktemp)
TMP_CHANGED=$(mktemp)
TMP_REMOVED=$(mktemp)
TMP_OTHER=$(mktemp)

# Categorize commits
while IFS= read -r line; do
    HASH="${line%%||*}"
    SUBJECT="${line#*||}"
    
    # Lowercase subject for easy matching
    L_SUBJ=$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$L_SUBJ" == feat* ]] || [[ "$L_SUBJ" == add* ]]; then
        echo "- $SUBJECT ($HASH)" >> "$TMP_ADDED"
    elif [[ "$L_SUBJ" == fix* ]] || [[ "$L_SUBJ" == bug* ]]; then
        echo "- $SUBJECT ($HASH)" >> "$TMP_FIXED"
    elif [[ "$L_SUBJ" == refactor* ]] || [[ "$L_SUBJ" == chore* ]] || [[ "$L_SUBJ" == update* ]] || [[ "$L_SUBJ" == change* ]] || [[ "$L_SUBJ" == perf* ]]; then
        echo "- $SUBJECT ($HASH)" >> "$TMP_CHANGED"
    elif [[ "$L_SUBJ" == remove* ]] || [[ "$L_SUBJ" == delete* ]] || [[ "$L_SUBJ" == drop* ]]; then
        echo "- $SUBJECT ($HASH)" >> "$TMP_REMOVED"
    else
        echo "- $SUBJECT ($HASH)" >> "$TMP_OTHER"
    fi
done <<< "$COMMITS"

DATE_STR=$(date +%Y-%m-%d)
NEW_CONTENT="# Changelog\n\n## [Unreleased] - $DATE_STR\n"

if [ "$LAST_TAG_MSG" != "Initial" ]; then
    NEW_CONTENT+="\nChanges since tag: \`$LAST_TAG_MSG\`\n\n"
fi

if [ -s "$TMP_ADDED" ]; then
    NEW_CONTENT+="### Added\n$(cat "$TMP_ADDED")\n\n"
fi
if [ -s "$TMP_FIXED" ]; then
    NEW_CONTENT+="### Fixed\n$(cat "$TMP_FIXED")\n\n"
fi
if [ -s "$TMP_CHANGED" ]; then
    NEW_CONTENT+="### Changed\n$(cat "$TMP_CHANGED")\n\n"
fi
if [ -s "$TMP_REMOVED" ]; then
    NEW_CONTENT+="### Removed\n$(cat "$TMP_REMOVED")\n\n"
fi
if [ -s "$TMP_OTHER" ]; then
    NEW_CONTENT+="### Other\n$(cat "$TMP_OTHER")\n\n"
fi

rm "$TMP_ADDED" "$TMP_FIXED" "$TMP_CHANGED" "$TMP_REMOVED" "$TMP_OTHER"

if [ -f "CHANGELOG.md" ]; then
    EXISTING=$(sed '1,2d' CHANGELOG.md)
    echo -e "$NEW_CONTENT---\n$EXISTING" > CHANGELOG.md
else
    echo -e "$NEW_CONTENT" > CHANGELOG.md
fi

echo "Successfully generated/updated CHANGELOG.md"
