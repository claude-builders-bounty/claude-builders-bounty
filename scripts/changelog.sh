#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
VERSION="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "v1.0.0")}"
DATE=$(date +%Y-%m-%d)

# Get previous tag or first commit
PREV_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$PREV_TAG" ]; then
    RANGE_ARGS="HEAD"
else
    RANGE_ARGS="$PREV_TAG..HEAD"
fi

echo "Generating changelog for range: $RANGE_ARGS..."

# Extract commits
COMMITS=$(git log $RANGE_ARGS --pretty=format:"%s (%h)")

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    
    # Lowercase check for categorization
    lower_line=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$lower_line" =~ ^feat ]] || [[ "$lower_line" =~ add ]]; then
        ADDED="$ADDED\n- ${line#* }";
    elif [[ "$lower_line" =~ ^fix ]] || [[ "$lower_line" =~ bug ]]; then
        FIXED="$FIXED\n- ${line#* }";
    elif [[ "$lower_line" =~ ^refactor ]] || [[ "$lower_line" =~ ^perf ]] || [[ "$lower_line" =~ change ]] || [[ "$lower_line" =~ update ]]; then
        CHANGED="$CHANGED\n- ${line#* }";
    elif [[ "$lower_line" =~ ^remove ]] || [[ "$lower_line" =~ ^delete ]] || [[ "$lower_line" =~ deprecate ]]; then
        REMOVED="$REMOVED\n- ${line#* }";
    else
        CHANGED="$CHANGED\n- $line";
    fi
done <<< "$COMMITS"

# Build new section
NEW_SECTION="## [$VERSION] - $DATE"

if [ -n "$ADDED" ]; then
    NEW_SECTION="$NEW_SECTION\n\n### Added$ADDED"
fi
if [ -n "$CHANGED" ]; then
    NEW_SECTION="$NEW_SECTION\n\n### Changed$CHANGED"
fi
if [ -n "$FIXED" ]; then
    NEW_SECTION="$NEW_SECTION\n\n### Fixed$FIXED"
fi
if [ -n "$REMOVED" ]; then
    NEW_SECTION="$NEW_SECTION\n\n### Removed$REMOVED"
fi

# Prepend to existing changelog or create new
if [ -f "$OUTPUT_FILE" ]; then
    TEMP_FILE=$(mktemp)
    echo -e "# Changelog\n" > "$TEMP_FILE"
    echo -e "$NEW_SECTION\n" >> "$TEMP_FILE"
    tail -n +3 "$OUTPUT_FILE" >> "$TEMP_FILE" || true
    mv "$TEMP_FILE" "$OUTPUT_FILE"
else
    echo -e "# Changelog\n\n$NEW_SECTION" > "$OUTPUT_FILE"
fi

echo "Successfully updated $OUTPUT_FILE!"
