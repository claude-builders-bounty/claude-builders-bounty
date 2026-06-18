#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history

# Find the latest git tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    # If no tags exist, get all commits
    LOGS=$(git log --pretty=format:"%s")
else
    # Get commits since the last tag
    LOGS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s")
fi

if [ -z "$LOGS" ]; then
    echo "No commits found since the last tag. Exiting."
    exit 0
fi

# Categorization buckets
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

# Parse and categorize each commit
while IFS= read -r msg; do
    lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lower" == add* ]] || [[ "$lower" == feat* ]]; then
        ADDED="${ADDED}- ${msg}\n"
    elif [[ "$lower" == fix* ]] || [[ "$lower" == bug* ]]; then
        FIXED="${FIXED}- ${msg}\n"
    elif [[ "$lower" == change* ]] || [[ "$lower" == update* ]] || [[ "$lower" == refactor* ]] || [[ "$lower" == chore* ]]; then
        CHANGED="${CHANGED}- ${msg}\n"
    elif [[ "$lower" == remove* ]] || [[ "$lower" == delete* ]] || [[ "$lower" == drop* ]]; then
        REMOVED="${REMOVED}- ${msg}\n"
    else
        # Fallback for uncategorized commits
        OTHER="${OTHER}- ${msg}\n"
    fi
done <<< "$LOGS"

DATE=$(date '+%Y-%m-%d')
OUT_FILE="CHANGELOG.md"

# Generate the Markdown file
{
    echo "# Changelog"
    echo "Generated on $DATE"
    echo ""
    
    if [ -n "$ADDED" ]; then
        echo "## Added"
        echo -e "$ADDED"
    fi
    
    if [ -n "$FIXED" ]; then
        echo "## Fixed"
        echo -e "$FIXED"
    fi
    
    if [ -n "$CHANGED" ]; then
        echo "## Changed"
        echo -e "$CHANGED"
    fi
    
    if [ -n "$REMOVED" ]; then
        echo "## Removed"
        echo -e "$REMOVED"
    fi
    
    if [ -n "$OTHER" ]; then
        echo "## Other"
        echo -e "$OTHER"
    fi
} > "$OUT_FILE"

echo "Success: $OUT_FILE has been generated and auto-categorized!"
