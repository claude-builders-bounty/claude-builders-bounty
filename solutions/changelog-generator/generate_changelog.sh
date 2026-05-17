#!/bin/bash
# Generate a structured CHANGELOG.md from git history since the last tag.

OUTPUT_FILE="CHANGELOG.md"

# 1. Get the most recent tag. If no tags exist, get the first commit.
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Getting all commits from the beginning."
    GIT_RANGE=""
else
    echo "Generating changelog since tag: $LAST_TAG"
    GIT_RANGE="$LAST_TAG..HEAD"
fi

# 2. Extract commit messages into a temporary file
TMP_FILE=$(mktemp)
git log $GIT_RANGE --oneline --pretty=format:"%s|%h" > "$TMP_FILE"

# Prepare variables for categories
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHERS=""

# 3. Categorize commits based on conventional commit prefixes
while IFS='|' read -r msg hash; do
    # Skip empty lines
    [ -z "$msg" ] && continue
    
    # プレフィックスを消した綺麗版
    CLEAN_MSG=$(echo "$msg" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?:[[:space:]]*//')
    
    # Repo URLの取得（失敗した場合はただのハッシュテキストにする）
    REPO_URL=$(git config --get remote.origin.url | sed -E 's/.*github\.com[\/:]//g' | sed 's/\.git$//')
    ENTRY="- $CLEAN_MSG ([${hash}](https://github.com/${REPO_URL}/commit/${hash}))"

    # Categorize based on prefix (case insensitive)
    if echo "$msg" | grep -qiE "^(feat|add)(\([^)]*\))?:"; then
        ADDED="$ADDED\n$ENTRY"
    elif echo "$msg" | grep -qiE "^(fix|bug)(\([^)]*\))?:"; then
        FIXED="$FIXED\n$ENTRY"
    elif echo "$msg" | grep -qiE "^(refactor|chore|style|perf|docs|test)(\([^)]*\))?:"; then
        CHANGED="$CHANGED\n$ENTRY"
    elif echo "$msg" | grep -qiE "^(remove|del|drop)(\([^)]*\))?:"; then
        REMOVED="$REMOVED\n$ENTRY"
    else
        # If it doesn't match convention, put in Others
        OTHERS="$OTHERS\n- $msg ([${hash}](...))"
    fi
done < "$TMP_FILE"

rm "$TMP_FILE"

# 4. Generate the CHANGELOG.md output
DATE=$(date +'%Y-%m-%d')
echo "# Changelog" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## [Unreleased] - $DATE" >> "$OUTPUT_FILE"

has_content=false

if [ -n "$ADDED" ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "### Added" >> "$OUTPUT_FILE"
    echo -e "$ADDED" | sed '/^$/d' >> "$OUTPUT_FILE"
    has_content=true
fi

if [ -n "$FIXED" ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "### Fixed" >> "$OUTPUT_FILE"
    echo -e "$FIXED" | sed '/^$/d' >> "$OUTPUT_FILE"
    has_content=true
fi

if [ -n "$CHANGED" ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "### Changed" >> "$OUTPUT_FILE"
    echo -e "$CHANGED" | sed '/^$/d' >> "$OUTPUT_FILE"
    has_content=true
fi

if [ -n "$REMOVED" ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "### Removed" >> "$OUTPUT_FILE"
    echo -e "$REMOVED" | sed '/^$/d' >> "$OUTPUT_FILE"
    has_content=true
fi

if [ -n "$OTHERS" ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "### Other" >> "$OUTPUT_FILE"
    echo -e "$OTHERS" | sed '/^$/d' >> "$OUTPUT_FILE"
    has_content=true
fi

if [ "$has_content" = false ]; then
    echo "No significant changes found in this release." >> "$OUTPUT_FILE"
fi

echo ""
echo "✅ Changelog generated successfully at $OUTPUT_FILE"
