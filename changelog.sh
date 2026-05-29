#!/bin/bash

# changelog.sh - Generate a structured CHANGELOG.md from git history

set -euo pipefail

# Function to categorize commit messages
categorize_commit() {
    local subject="$1"
    subject_lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    
    # Check for keywords in the commit subject
    if [[ "$subject_lower" =~ (added|feat|feature) ]]; then
        echo "Added"
    elif [[ "$subject_lower" =~ (fixed|fix|bugfix) ]]; then
        echo "Fixed"
    elif [[ "$subject_lower" =~ (changed|change|refactor|perf|performance) ]]; then
        echo "Changed"
    elif [[ "$subject_lower" =~ (deprecated|deprecation) ]]; then
        echo "Deprecated"
    elif [[ "$subject_lower" =~ (removed|remove|delete) ]]; then
        echo "Removed"
    elif [[ "$subject_lower" =~ (security|sec) ]]; then
        echo "Security"
    else
        # Default to Changed if no match
        echo "Changed"
    fi
}

# Get the last tag, if any
last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$last_tag" ]; then
    # No tags, start from the beginning
    range=""
    echo "No tags found, generating changelog from the beginning of history."
else
    range="${last_tag}..HEAD"
fi

# Get commit subjects since last tag (or all if no tags)
if [ -z "$range" ]; then
    commits=$(git log --pretty=format:"%s")
else
    commits=$(git log "$range" --pretty=format:"%s")
fi

# Initialize categories
declare -A categories
categories["Added"]=""
categories["Fixed"]=""
categories["Changed"]=""
categories["Deprecated"]=""
categories["Removed"]=""
categories["Security"]=""

# Process each commit
while IFS= read -r subject; do
    if [ -z "$subject" ]; then
        continue
    fi
    category=$(categorize_commit "$subject")
    # Append the commit subject to the category list
    if [ -z "${categories[$category]}" ]; then
        categories[$category]="- $subject"
    else
        categories[$category]="${categories[$category]}
- $subject"
    fi
done <<< "$commits"

# Generate changelog content
today=$(date +"%Y-%m-%d")
cat << EOF
# Changelog

## [Unreleased] - $today

EOF

# Output each category that has commits
for cat in Added Fixed Changed Deprecated Removed Security; do
    if [ -n "${categories[$cat]}" ]; then
        echo "### $cat"
        echo "${categories[$cat]}"
        echo ""
    fi
done

EOF

# Optionally, write to CHANGELOG.md if an argument is given
if [ $# -eq 1 ] && [ "$1" = "--write" ]; then
    # Generate the changelog and write to CHANGELOG.md
    # We'll reuse the above logic but write to file
    # For simplicity, we'll just call ourselves and redirect
    "$0" > CHANGELOG.md
    echo "Changelog written to CHANGELOG.md"
fi