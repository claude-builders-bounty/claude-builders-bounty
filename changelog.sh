#!/bin/bash

# Generate Changelog from Git History
# Usage: bash changelog.sh [output_file]

set -e

OUTPUT_FILE="${1:-CHANGELOG.md}"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not a git repository"
    exit 1
fi

# Get the last tag, or use initial commit if no tags exist
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
    # No tags found, get all commits
    RANGE="HEAD"
    VERSION="Unreleased"
    DATE=$(date +%Y-%m-%d)
else
    RANGE="${LAST_TAG}..HEAD"
    VERSION="$LAST_TAG"
    DATE=$(git log -1 --format=%ad --date=short "$LAST_TAG")
fi

# Get project name from remote URL or directory name
PROJECT_NAME=$(basename -s .git "$(git remote get-url origin 2>/dev/null)" 2>/dev/null || basename "$(pwd)")

# Initialize arrays for categorized commits
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

# Process commits
while IFS= read -r line; do
    HASH=$(echo "$line" | cut -d'|' -f1)
    MSG=$(echo "$line" | cut -d'|' -f2-)
    
    # Skip merge commits
    if [[ "$MSG" == Merge* ]]; then
        continue
    fi
    
    # Categorize based on conventional commits or keywords
    LOWER_MSG=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$LOWER_MSG" == feat:* ]] || [[ "$LOWER_MSG" == feature:* ]] || [[ "$LOWER_MSG" == add:* ]] || [[ "$LOWER_MSG" == added:* ]]; then
        ADDED+=("- $MSG")
    elif [[ "$LOWER_MSG" == fix:* ]] || [[ "$LOWER_MSG" == bugfix:* ]] || [[ "$LOWER_MSG" == patch:* ]]; then
        FIXED+=("- $MSG")
    elif [[ "$LOWER_MSG" == remove:* ]] || [[ "$LOWER_MSG" == deleted:* ]] || [[ "$LOWER_MSG" == delete:* ]]; then
        REMOVED+=("- $MSG")
    else
        CHANGED+=("- $MSG")
    fi
done < <(git log --oneline --no-merges --format="%h|%s" $RANGE 2>/dev/null)

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to $PROJECT_NAME will be documented in this file."
    echo ""
    echo "## [$VERSION] - $DATE"
    echo ""
    
    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        echo ""
        printf '%s\n' "${ADDED[@]}"
        echo ""
    fi
    
    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        echo ""
        printf '%s\n' "${FIXED[@]}"
        echo ""
    fi
    
    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        echo ""
        printf '%s\n' "${CHANGED[@]}"
        echo ""
    fi
    
    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        echo ""
        printf '%s\n' "${REMOVED[@]}"
        echo ""
    fi
    
    # If no commits were categorized, add a placeholder
    if [ ${#ADDED[@]} -eq 0 ] && [ ${#FIXED[@]} -eq 0 ] && [ ${#CHANGED[@]} -eq 0 ] && [ ${#REMOVED[@]} -eq 0 ]; then
        echo "No changes recorded."
        echo ""
    fi
} > "$OUTPUT_FILE"

echo "Changelog generated: $OUTPUT_FILE"
echo "Version: $VERSION"
echo "Date: $DATE"
echo "Commits analyzed: $(git log --oneline --no-merges $RANGE 2>/dev/null | wc -l | tr -d ' ')"
