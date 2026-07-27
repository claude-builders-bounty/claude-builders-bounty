#!/bin/bash
# CHANGELOG Generator - generates structured CHANGELOG.md from git history
# Usage: bash changelog.sh [since_tag]
# Byaigo - github.com/Byaigo

SINCE_TAG="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo '')}"
OUTPUT="CHANGELOG.md"
TEMP=$(mktemp)
VERSION=$(git describe --tags --always 2>/dev/null || echo "unreleased")
DATE=$(date +%Y-%m-%d)

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "## [$VERSION] - $DATE" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Get commits since last tag or all commits
if [ -n "$SINCE_TAG" ]; then
    git log "${SINCE_TAG}..HEAD" --pretty=format:"%s" > "$TEMP"
else
    git log --pretty=format:"%s" > "$TEMP"
fi

# Categorize commits
declare -A CATEGORIES
CATEGORIES["Added"]="### Added\n"
CATEGORIES["Fixed"]="### Fixed\n"
CATEGORIES["Changed"]="### Changed\n"
CATEGORIES["Removed"]="### Removed\n"
CATEGORIES["Other"]="### Other\n"

declare -A COUNTS

while IFS= read -r line; do
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    [ -z "$line" ] && continue
    
    msg_lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    
    if echo "$msg_lower" | grep -qE "^(add|feat|new|create|implement|introduce)"; then
        CATEGORIES["Added"]+="- $line\n"
        COUNTS["Added"]=$((${COUNTS["Added"]:-0}+1))
    elif echo "$msg_lower" | grep -qE "^(fix|bug|resolve|patch|repair|hotfix)"; then
        CATEGORIES["Fixed"]+="- $line\n"
        COUNTS["Fixed"]=$((${COUNTS["Fixed"]:-0}+1))
    elif echo "$msg_lower" | grep -qE "^(change|update|modify|refactor|improve|enhance|tweak|adjust)"; then
        CATEGORIES["Changed"]+="- $line\n"
        COUNTS["Changed"]=$((${COUNTS["Changed"]:-0}+1))
    elif echo "$msg_lower" | grep -qE "^(remove|delete|drop|deprecate|retire)"; then
        CATEGORIES["Removed"]+="- $line\n"
        COUNTS["Removed"]=$((${COUNTS["Removed"]:-0}+1))
    else
        CATEGORIES["Other"]+="- $line\n"
        COUNTS["Other"]=$((${COUNTS["Other"]:-0}+1))
    fi
done < "$TEMP"

# Write categorized changes
for CAT in "Added" "Fixed" "Changed" "Removed" "Other"; do
    if [ "${COUNTS[$CAT]:-0}" -gt 0 ]; then
        echo -e "${CATEGORIES[$CAT]}" >> "$OUTPUT"
    fi
done

rm -f "$TEMP"

echo "✅ CHANGELOG.md generated with:"
for CAT in "Added" "Fixed" "Changed" "Removed" "Other"; do
    count="${COUNTS[$CAT]:-0}"
    [ "$count" -gt 0 ] && echo "   $CAT: $count commits"
done
echo ""
echo "📄 Output: $OUTPUT"
echo "🆓 Free tool by Byaigo | github.com/Byaigo"
