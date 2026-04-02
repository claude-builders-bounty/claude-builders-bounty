#!/bin/bash

# CHANGELOG Generator - Automatically generates structured CHANGELOG.md from git history
# Usage: ./changelog.sh [output_file]
# If no output file is specified, outputs to stdout

set -e

OUTPUT_FILE="${1:-/dev/stdout}"
TEMP_FILE=$(mktemp)

# Function to categorize commits based on conventional commit prefixes
categorize_commits() {
    local category="$1"
    shift
    local commits=("$@")
    
    if [ ${#commits[@]} -gt 0 ]; then
        echo "### $category" >> "$TEMP_FILE"
        for commit in "${commits[@]}"; do
            # Extract commit message (remove hash and first word if it's a conventional commit type)
            local msg=$(echo "$commit" | cut -d' ' -f2-)
            # Clean up conventional commit prefixes
            msg=$(echo "$msg" | sed -E 's/^(feat|feature|add|added)[(: ]+/✅ /i')
            msg=$(echo "$msg" | sed -E 's/^(fix|bug|fixed|patch)[(: ]+/🐛 /i')
            msg=$(echo "$msg" | sed -E 's/^(change|changed|update|updated|refactor|perf)[(: ]+/🔄 /i')
            msg=$(echo "$msg" | sed -E 's/^(remove|removed|delete|deleted)[(: ]+/🗑️ /i')
            echo "- $msg" >> "$TEMP_FILE"
        done
        echo "" >> "$TEMP_FILE"
    fi
}

# Get the last git tag, or use empty string if none exists
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
    COMMIT_RANGE="$LAST_TAG..HEAD"
    echo "# Changelog" > "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    echo "## $(git describe --tags --exact-match HEAD 2>/dev/null || git rev-parse --short HEAD)" >> "$TEMP_FILE"
else
    COMMIT_RANGE="HEAD"
    echo "# Changelog" > "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    echo "## Unreleased" >> "$TEMP_FILE"
fi

echo "" >> "$TEMP_FILE"

# Get all commits in the range
ALL_COMMITS=$(git log --oneline --reverse "$COMMIT_RANGE" 2>/dev/null || echo "")

# Initialize arrays for each category
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Categorize commits based on keywords in commit messages
while IFS= read -r commit; do
    if [ -n "$commit" ]; then
        commit_lower=$(echo "$commit" | tr '[:upper:]' '[:lower:]')
        
        # Check for Added/Feature keywords
        if [[ "$commit_lower" == feat:* ]] || [[ "$commit_lower" == feature:* ]] || \
           [[ "$commit_lower" == add:* ]] || [[ "$commit_lower" == added:* ]] || \
           [[ "$commit_lower" == *add* ]] || [[ "$commit_lower" == *new* ]] || \
           [[ "$commit_lower" == *create* ]] || [[ "$commit_lower" == *implement* ]]; then
            ADDED+=("$commit")
        # Check for Fixed/Bug keywords
        elif [[ "$commit_lower" == fix:* ]] || [[ "$commit_lower" == bug:* ]] || \
             [[ "$commit_lower" == fixed:* ]] || [[ "$commit_lower" == patch:* ]] || \
             [[ "$commit_lower" == *fix* ]] || [[ "$commit_lower" == *bug* ]] || \
             [[ "$commit_lower" == *error* ]] || [[ "$commit_lower" == *issue* ]]; then
            FIXED+=("$commit")
        # Check for Removed/Delete keywords
        elif [[ "$commit_lower" == remove:* ]] || [[ "$commit_lower" == removed:* ]] || \
             [[ "$commit_lower" == delete:* ]] || [[ "$commit_lower" == deleted:* ]] || \
             [[ "$commit_lower" == *remove* ]] || [[ "$commit_lower" == *delete* ]] || \
             [[ "$commit_lower" == *drop* ]] || [[ "$commit_lower" == *deprecate* ]]; then
            REMOVED+=("$commit")
        # Everything else goes to Changed
        else
            CHANGED+=("$commit")
        fi
    fi
done <<< "$ALL_COMMITS"

# Output categorized commits
has_content=false
if [ ${#ADDED[@]} -gt 0 ]; then
    categorize_commits "Added" "${ADDED[@]}"
    has_content=true
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    categorize_commits "Fixed" "${FIXED[@]}"
    has_content=true
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    categorize_commits "Changed" "${CHANGED[@]}"
    has_content=true
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    categorize_commits "Removed" "${REMOVED[@]}"
    has_content=true
fi

# If no commits found, add a placeholder
if [ "$has_content" = false ]; then
    echo "No changes since last release." >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
fi

# Move temp file to output
if [ "$OUTPUT_FILE" = "/dev/stdout" ]; then
    cat "$TEMP_FILE"
else
    mv "$TEMP_FILE" "$OUTPUT_FILE"
fi

# Clean up if temp file still exists
[ -f "$TEMP_FILE" ] && rm -f "$TEMP_FILE"