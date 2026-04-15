#!/bin/bash

# ==============================================================================
# Automated Changelog Generator
# Generates a structured CHANGELOG.md based on Conventional Commit standards.
# ==============================================================================

OUTPUT_FILE="CHANGELOG.md"
TIMESTAMP=$(date +%Y-%m-%d)

# Ensure we are in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: This script must be run from the root of a git repository."
    exit 1
fi

echo "Generating changelog..."

# Initialize the file with a header
cat <<EOF > "$OUTPUT_FILE"
# Changelog

All notable changes to this project will be documented in this file.
Changes are grouped by type following Conventional Commit standards.

EOF

# Determine the range for the changelog
# Try to get the last tag; if none exists, start from the first commit.
START_REF=$(git describe --tags $(git rev-list --max-parents=0 HEAD) 2>/dev/null || git rev-list --max-parents=0 HEAD)
END_REF="HEAD"

echo "## [$TIMESTAMP] (Range: $START_REF..$END_REF)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Define commit categories for filtering
# Format: [prefix]="Display Name"
declare -A CATEGORIES=( 
    ["feat"]="Features" 
    ["fix"]="Bug Fixes" 
    ["docs"]="Documentation" 
    ["perf"]="Performance Improvements" 
    ["refactor"]="Code Refactoring" 
    ["chore"]="Maintenance" 
)

# Process each defined category
for key in "${!CATEGORIES[@]}"; do
    # Extract commits matching the prefix (e.g., "feat:" or "feat(")
    COMMITS=$(git log "$START_REF..$END_REF" --grep="^$key($)" --grep="^$key:" --pretty=format:"- %s (%h)")
    
    if [ -n "$COMMITS" ]; then
        echo "### ${CATEGORIES[$key]}" >> "$OUTPUT_FILE"
        echo "$COMMITS" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    fi
done

# Handle any commits that didn't fit into the standard categories
MISC=$(git log "$START_REF..$END_REF" --invert-grep="^feat(|^fix(|^docs(|^perf(|^refactor(|^chore(" --pretty=format:"- %s (%h)")
if [ -n "$MISC" ]; then
    echo "### Other Changes" >> "$OUTPUT_FILE"
    echo "$MISC" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
fi

echo "Success: $OUTPUT_FILE has been generated."
