#!/bin/bash
# changelog.sh
# Generates a structured CHANGELOG.md from git history since the last tag.

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    echo "No previous tags found. Fetching all commits."
    COMMITS=$(git log --pretty=format:"%s")
else
    echo "Fetching commits since $LAST_TAG"
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s")
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r msg; do
    # Convert to lowercase for matching
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lower_msg" == feat* ]] || [[ "$lower_msg" == add* ]]; then
        ADDED="$ADDED\n- $msg"
    elif [[ "$lower_msg" == fix* ]] || [[ "$lower_msg" == bug* ]]; then
        FIXED="$FIXED\n- $msg"
    elif [[ "$lower_msg" == change* ]] || [[ "$lower_msg" == refactor* ]] || [[ "$lower_msg" == update* ]] || [[ "$lower_msg" == chore* ]]; then
        CHANGED="$CHANGED\n- $msg"
    elif [[ "$lower_msg" == remove* ]] || [[ "$lower_msg" == delete* ]]; then
        REMOVED="$REMOVED\n- $msg"
    else
        OTHER="$OTHER\n- $msg"
    fi
done <<< "$COMMITS"

DATE=$(date +%Y-%m-%d)
OUT="CHANGELOG.md"

echo "# Changelog ($DATE)" > $OUT
echo "" >> $OUT

if [ -n "$ADDED" ]; then
    echo "## Added" >> $OUT
    echo -e "$ADDED" | sed '/^$/d' >> $OUT
    echo "" >> $OUT
fi

if [ -n "$FIXED" ]; then
    echo "## Fixed" >> $OUT
    echo -e "$FIXED" | sed '/^$/d' >> $OUT
    echo "" >> $OUT
fi

if [ -n "$CHANGED" ]; then
    echo "## Changed" >> $OUT
    echo -e "$CHANGED" | sed '/^$/d' >> $OUT
    echo "" >> $OUT
fi

if [ -n "$REMOVED" ]; then
    echo "## Removed" >> $OUT
    echo -e "$REMOVED" | sed '/^$/d' >> $OUT
    echo "" >> $OUT
fi

if [ -n "$OTHER" ]; then
    echo "## Other" >> $OUT
    echo -e "$OTHER" | sed '/^$/d' >> $OUT
    echo "" >> $OUT
fi

echo "Changelog successfully generated at $OUT"
