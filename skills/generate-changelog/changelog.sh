#!/bin/bash
# Changelog Generator - Auto-generate CHANGELOG.md from git history
# Usage: bash changelog.sh

set -e

# Get the last git tag (or first commit if no tags)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

# Get current date in ISO format
CURRENT_DATE=$(date +%Y-%m-%d)

# Get commits since last tag
COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%h|%s" --reverse)

# Initialize category arrays
declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()
declare -a other=()

# Categorize commits based on conventional commit prefixes
while IFS='|' read -r hash message; do
    # Convert to lowercase for matching
    lower_message=$(echo "$message" | tr '[:upper:]' '[:lower:]')

    # Categorize based on prefix
    if [[ "$lower_message" =~ ^(feat|add|new): ]]; then
        added+=("- $message ($hash)")
    elif [[ "$lower_message" =~ ^(fix|bugfix|bug): ]]; then
        fixed+=("- $message ($hash)")
    elif [[ "$lower_message" =~ ^(change|update|refactor|improve|chore): ]]; then
        changed+=("- $message ($hash)")
    elif [[ "$lower_message" =~ ^(remove|delete|deprecate): ]]; then
        removed+=("- $message ($hash)")
    else
        # Try to detect from keywords in message
        if [[ "$lower_message" =~ (add|new|feature|implement) ]]; then
            added+=("- $message ($hash)")
        elif [[ "$lower_message" =~ (fix|bug|resolve|patch) ]]; then
            fixed+=("- $message ($hash)")
        elif [[ "$lower_message" =~ (update|change|refactor|improve|modify) ]]; then
            changed+=("- $message ($hash)")
        elif [[ "$lower_message" =~ (remove|delete|deprecate) ]]; then
            removed+=("- $message ($hash)")
        else
            other+=("- $message ($hash)")
        fi
    fi
done <<< "$COMMITS"

# Generate CHANGELOG content
echo "# Changelog"
echo ""
echo "All notable changes to this project will be documented in this file."
echo ""
echo "## [Unreleased] - $CURRENT_DATE"
echo ""

# Output categories if they have entries
if [ ${#added[@]} -gt 0 ]; then
    echo "### Added"
    echo ""
    for item in "${added[@]}"; do
        echo "$item"
    done
    echo ""
fi

if [ ${#changed[@]} -gt 0 ]; then
    echo "### Changed"
    echo ""
    for item in "${changed[@]}"; do
        echo "$item"
    done
    echo ""
fi

if [ ${#fixed[@]} -gt 0 ]; then
    echo "### Fixed"
    echo ""
    for item in "${fixed[@]}"; do
        echo "$item"
    done
    echo ""
fi

if [ ${#removed[@]} -gt 0 ]; then
    echo "### Removed"
    echo ""
    for item in "${removed[@]}"; do
        echo "$item"
    done
    echo ""
fi

if [ ${#other[@]} -gt 0 ]; then
    echo "### Other"
    echo ""
    for item in "${other[@]}"; do
        echo "$item"
    done
    echo ""
fi

# Show summary
total_commits=$((${#added[@]} + ${#changed[@]} + ${#fixed[@]} + ${#removed[@]} + ${#other[@]}))
echo "---"
echo ""
echo "**Summary:** $total_commits commits since ${LAST_TAG}"
echo ""
echo "Generated on: $CURRENT_DATE"
