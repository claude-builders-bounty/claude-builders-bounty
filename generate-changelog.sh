#!/bin/bash
# Generate structured CHANGELOG from git history

OUTPUT_FILE="CHANGELOG.md"
DATE=$(date '+%Y-%m-%d')

echo "# Changelog" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "## [$DATE]" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Get commits by category
echo "### Features" >> "$OUTPUT_FILE"
git log --oneline --grep="feat" | head -10 | while read commit; do
    echo "- $commit" >> "$OUTPUT_FILE"
done

echo "" >> "$OUTPUT_FILE"
echo "### Fixes" >> "$OUTPUT_FILE"
git log --oneline --grep="fix" | head -10 | while read commit; do
    echo "- $commit" >> "$OUTPUT_FILE"
done

echo "" >> "$OUTPUT_FILE"
echo "### Other" >> "$OUTPUT_FILE"
git log --oneline --grep="chore\|docs\|refactor" | head -10 | while read commit; do
    echo "- $commit" >> "$OUTPUT_FILE"
done

echo "CHANGELOG.md generated successfully!"
