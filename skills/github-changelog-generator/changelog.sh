#!/bin/bash

# CHANGELOG Generator
# Usage: bash changelog.sh [output_file] [max_commits]
# 
# Generates a structured CHANGELOG.md from git history
# Categorizes commits by type: Added, Fixed, Changed, Removed

set -e

OUTPUT_FILE="${1:-CHANGELOG.md}"
MAX_COMMITS="${2:-100}"

# Check if in git repository
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "❌ Error: Not in a git repository"
    exit 1
}

echo "🔍 Generating CHANGELOG from git history..."
echo "   Repository: $REPO_ROOT"
echo "   Max commits: $MAX_COMMITS"
echo ""

# Initialize arrays for each category
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

# Get git log
COMMITS=$(git log --pretty=format:"%h|%s|%ai" --no-merges -n "$MAX_COMMITS")

# Process each commit
while IFS='|' read -r hash message date; do
    # Skip empty lines
    [[ -z "$hash" ]] && continue
    
    # Convert to lowercase for matching
    msg_lower=$(echo "$message" | tr '[:upper:]' '[:lower:]')
    
    # Classify by commit type
    if [[ "$msg_lower" =~ ^feat:|^feat\(|^feature:|^add:|^add\( ]]; then
        ADDED+=("- $message ($hash)")
    elif [[ "$msg_lower" =~ ^fix:|^fix\(|^bugfix:|^bug: ]]; then
        FIXED+=("- $message ($hash)")
    elif [[ "$msg_lower" =~ ^refactor:|^refactor\(|^change:|^change\(|^update:|^update\(|^improve:|^style:|^docs:|^test:|^chore: ]]; then
        CHANGED+=("- $message ($hash)")
    elif [[ "$msg_lower" =~ ^remove:|^remove\(|^drop:|^drop\(|^delete:|^deprecate:|^revert: ]]; then
        REMOVED+=("- $message ($hash)")
    else
        OTHER+=("- $message ($hash)")
    fi
done <<< "$COMMITS"

# Write CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "## [Unreleased]"
    echo ""
    
    # Added section
    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        for item in "${ADDED[@]}"; do
            echo "$item"
        done
        echo ""
    fi
    
    # Fixed section
    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        for item in "${FIXED[@]}"; do
            echo "$item"
        done
        echo ""
    fi
    
    # Changed section
    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        for item in "${CHANGED[@]}"; do
            echo "$item"
        done
        echo ""
    fi
    
    # Removed section
    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        for item in "${REMOVED[@]}"; do
            echo "$item"
        done
        echo ""
    fi
    
    # Other section (if any)
    if [ ${#OTHER[@]} -gt 0 ]; then
        echo "### Other"
        for item in "${OTHER[@]}"; do
            echo "$item"
        done
        echo ""
    fi
} > "$OUTPUT_FILE"

# Summary
TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]}))
echo "✅ CHANGELOG generated: $OUTPUT_FILE"
echo ""
echo "📊 Summary:"
echo "   Total commits: $TOTAL"
[ ${#ADDED[@]} -gt 0 ] && echo "   - Added:   ${#ADDED[@]}"
[ ${#FIXED[@]} -gt 0 ] && echo "   - Fixed:   ${#FIXED[@]}"
[ ${#CHANGED[@]} -gt 0 ] && echo "   - Changed: ${#CHANGED[@]}"
[ ${#REMOVED[@]} -gt 0 ] && echo "   - Removed: ${#REMOVED[@]}"
[ ${#OTHER[@]} -gt 0 ] && echo "   - Other:   ${#OTHER[@]}"
