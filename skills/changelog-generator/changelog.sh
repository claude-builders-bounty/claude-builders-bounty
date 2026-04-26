#!/bin/bash
# Generate structured CHANGELOG.md from git history
# Usage: ./changelog.sh [output_file]

set -e

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
REPO_NAME=$(basename -s .git "$REPO_URL" 2>/dev/null || echo "Repository")

# Get the last tag, or use the first commit if no tags
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    echo "Error: Could not determine last tag or initial commit"
    exit 1
fi

echo "Generating CHANGELOG from: $LAST_TAG"

# Get commits since last tag
COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%s" --no-merges 2>/dev/null || echo "")

if [ -z "$COMMITS" ]; then
    echo "No new commits since $LAST_TAG"
    exit 0
fi

# Categorize commits
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

while IFS= read -r line; do
    # Skip empty lines
    [ -z "$line" ] && continue
    
    # Categorize based on conventional commit prefixes
    lower_line=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    if echo "$lower_line" | grep -qE "^feat(\([^)]+\))?:|^add|^implement|^new"; then
        ADDED+=("$line")
    elif echo "$lower_line" | grep -qE "^fix(\([^)]+\))?:|^bugfix|^hotfix|^resolve"; then
        FIXED+=("$line")
    elif echo "$lower_line" | grep -qE "^refactor(\([^)]+\))?:|^update|^modify|^change|^improve|^optimize"; then
        CHANGED+=("$line")
    elif echo "$lower_line" | grep -qE "^remove(\([^)]+\))?:|^delete|^drop|^deprecate"; then
        REMOVED+=("$line")
    else
        # Default to Changed for uncategorized
        CHANGED+=("$line")
    fi
done <<< "$COMMITS"

# Generate CHANGELOG
DATE=$(date +%Y-%m-%d)

cat > "$OUTPUT_FILE" << HEADER
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - $DATE

HEADER

# Helper function to write section
write_section() {
    local title="$1"
    shift
    local -a items=("$@")
    
    if [ ${#items[@]} -gt 0 ]; then
        echo "### $title" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        for item in "${items[@]}"; do
            # Clean up the commit message - remove conventional commit prefixes
            clean_item=$(echo "$item" | sed -E 's/^[a-z]+(\([^)]+\))?:[[:space:]]*//i')
            echo "- $clean_item" >> "$OUTPUT_FILE"
        done
        echo "" >> "$OUTPUT_FILE"
    fi
}

write_section "Added" "${ADDED[@]}"
write_section "Fixed" "${FIXED[@]}"
write_section "Changed" "${CHANGED[@]}"
write_section "Removed" "${REMOVED[@]}"

echo "✅ CHANGELOG generated: $OUTPUT_FILE"
