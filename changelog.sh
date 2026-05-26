#!/bin/bash

# Fetch commits since the last tag, or all if no tag exists
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"%h %s")
    TITLE="All changes"
else
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%h %s")
    TITLE="Changes since tag: **$LAST_TAG**"
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

# Categorize commits
while IFS= read -r line; do
    [ -z "$line" ] && continue
    hash=$(echo "$line" | awk '{print $1}')
    message=$(echo "$line" | cut -d' ' -f2-)
    
    # Regex matching based on conventional commits and keywords
    if echo "$message" | grep -iqE "^(feat|add)"; then
        ADDED="$ADDED\n- \`$hash\` $message"
    elif echo "$message" | grep -iqE "^(fix|bug)"; then
        FIXED="$FIXED\n- \`$hash\` $message"
    elif echo "$message" | grep -iqE "^(remove|delete|revert|drop)"; then
        REMOVED="$REMOVED\n- \`$hash\` $message"
    else
        CHANGED="$CHANGED\n- \`$hash\` $message"
    fi
done <<< "$COMMITS"

# Generate CHANGELOG.md
OUTPUT_FILE="CHANGELOG.md"

echo "# Changelog" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "$TITLE" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Helper function to append section
append_section() {
    local header="$1"
    local content="$2"
    if [ -n "$(echo -e "$content" | tr -d '\n')" ]; then
        echo "## $header" >> "$OUTPUT_FILE"
        echo -e "$content" | sed '/^$/d' >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
}

append_section "Added" "$ADDED"
append_section "Fixed" "$FIXED"
append_section "Removed" "$REMOVED"
append_section "Changed" "$CHANGED"

echo "✅ Changelog generated successfully at $OUTPUT_FILE"
