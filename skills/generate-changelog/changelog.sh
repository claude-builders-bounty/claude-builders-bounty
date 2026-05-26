#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history since last tag

set -euo pipefail

# Output file
OUTPUT="CHANGELOG.md"

# Get the last tag, if any
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    LAST_TAG=$(git describe --tags --abbrev=0)
    COMMIT_RANGE="${LAST_TAG}..HEAD"
    echo "Generating changelog since tag: ${LAST_TAG}"
else
    COMMIT_RANGE=""
    echo "No tags found. Generating changelog from entire git history."
fi

# Define temporary files for categories
ADDED_FILE=$(mktemp)
CHANGED_FILE=$(mktemp)
FIXED_FILE=$(mktemp)
REMOVED_FILE=$(mktemp)

# Clean up temp files on exit
cleanup() {
    rm -f "$ADDED_FILE" "$CHANGED_FILE" "$FIXED_FILE" "$REMOVED_FILE"
}
trap cleanup EXIT

# Fetch commits
if [ -n "$COMMIT_RANGE" ]; then
    git log "$COMMIT_RANGE" --pretty=format:"%h %s (%an)" > raw_commits.txt || true
else
    git log --pretty=format:"%h %s (%an)" > raw_commits.txt || true
fi

# Check if there are any commits
if [ ! -s raw_commits.txt ]; then
    echo "No new commits found."
    rm -f raw_commits.txt
    exit 0
fi

# Categorize commits
while IFS= read -r line || [ -n "$line" ]; do
    # Remove hash for classification but keep it for reference
    hash=$(echo "$line" | cut -d' ' -f1)
    msg=$(echo "$line" | cut -d' ' -f2-)
    msg_lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

    formatted_line="- $msg [\`$hash\`]"

    # Logic to classify commit
    if [[ "$msg_lower" =~ ^(feat|add|new|create|implement) ]]; then
        echo "$formatted_line" >> "$ADDED_FILE"
    elif [[ "$msg_lower" =~ ^(fix|bug|patch|resolve) ]]; then
        echo "$formatted_line" >> "$FIXED_FILE"
    elif [[ "$msg_lower" =~ ^(remove|delete|rm) ]]; then
        echo "$formatted_line" >> "$REMOVED_FILE"
    else
        echo "$formatted_line" >> "$CHANGED_FILE"
    fi
done < raw_commits.txt
rm -f raw_commits.txt

# Start building CHANGELOG content
TEMP_OUT=$(mktemp)
DATE=$(date +"%Y-%m-%d")

echo "# Changelog" > "$TEMP_OUT"
echo "" >> "$TEMP_OUT"
echo "All notable changes to this project will be documented in this file." >> "$TEMP_OUT"
echo "" >> "$TEMP_OUT"

if [ -n "${LAST_TAG:-}" ]; then
    echo "## [Unreleased] - ${DATE}" >> "$TEMP_OUT"
else
    echo "## [Initial Release] - ${DATE}" >> "$TEMP_OUT"
fi
echo "" >> "$TEMP_OUT"

# Add sections if they have entries
if [ -s "$ADDED_FILE" ]; then
    echo "### Added" >> "$TEMP_OUT"
    cat "$ADDED_FILE" >> "$TEMP_OUT"
    echo "" >> "$TEMP_OUT"
fi

if [ -s "$CHANGED_FILE" ]; then
    echo "### Changed" >> "$TEMP_OUT"
    cat "$CHANGED_FILE" >> "$TEMP_OUT"
    echo "" >> "$TEMP_OUT"
fi

if [ -s "$FIXED_FILE" ]; then
    echo "### Fixed" >> "$TEMP_OUT"
    cat "$FIXED_FILE" >> "$TEMP_OUT"
    echo "" >> "$TEMP_OUT"
fi

if [ -s "$REMOVED_FILE" ]; then
    echo "### Removed" >> "$TEMP_OUT"
    cat "$REMOVED_FILE" >> "$TEMP_OUT"
    echo "" >> "$TEMP_OUT"
fi

# If output file already exists, prepend the new changelog details
if [ -f "$OUTPUT" ]; then
    # Keep the header from the old changelog and append new release under it
    # For simplicity, we can overwrite or append. Let's prepend to the existing file:
    echo "Appending new changes to existing ${OUTPUT}..."
    mv "$OUTPUT" old_changelog.md
    # Extract header if present, else just prepend
    cat "$TEMP_OUT" > "$OUTPUT"
    echo "" >> "$OUTPUT"
    cat old_changelog.md >> "$OUTPUT"
    rm -f old_changelog.md
else
    mv "$TEMP_OUT" "$OUTPUT"
fi

rm -f "$TEMP_OUT"
echo "Successfully generated/updated ${OUTPUT}!"
