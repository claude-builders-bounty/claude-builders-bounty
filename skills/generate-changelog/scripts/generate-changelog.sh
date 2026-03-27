#!/bin/bash
# SPDX-License-Identifier: MIT
# Generate CHANGELOG.md from git history
# Usage: ./generate-changelog.sh [output_file]

set -e

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_NAME=$(basename -s .git "$(git config --get remote.origin.url 2>/dev/null || echo 'project')")

# Get the latest tag, or empty if no tags exist
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Get commits since last tag (or all commits if no tag)
if [ -n "$LATEST_TAG" ]; then
    COMMIT_RANGE="$LATEST_TAG..HEAD"
    VERSION="Unreleased"
else
    COMMIT_RANGE="HEAD"
    VERSION="Unreleased"
fi

# Get all tags for historical versions
TAGS=$(git tag --sort=-v:refname 2>/dev/null || echo "")

# Function to categorize a commit
categorize_commit() {
    local message="$1"
    local category=""
    
    # Check commit type based on conventional commits prefix
    if [[ "$message" =~ ^feat(\(.+\))?:|^add:|^adding: ]]; then
        category="Added"
    elif [[ "$message" =~ ^fix(\(.+\))?:|^bugfix:|^fixing: ]]; then
        category="Fixed"
    elif [[ "$message" =~ ^remove:|^deprecate:|^deleted:|^removing: ]]; then
        category="Removed"
    elif [[ "$message" =~ ^refactor:|^perf:|^chore:|^change:|^changed:|^improve:|^update: ]]; then
        category="Changed"
    elif [[ "$message" =~ ^docs:|^doc: ]]; then
        category="Documentation"
    else
        # Fallback: check keywords in message
        lowercase_msg=$(echo "$message" | tr '[:upper:]' '[:lower:]')
        if [[ "$lowercase_msg" == *"add"* ]] || [[ "$lowercase_msg" == *"new feature"* ]] || [[ "$lowercase_msg" == *"implement"* ]]; then
            category="Added"
        elif [[ "$lowercase_msg" == *"fix"* ]] || [[ "$lowercase_msg" == *"bug"* ]] || [[ "$lowercase_msg" == *"issue"* ]]; then
            category="Fixed"
        elif [[ "$lowercase_msg" == *"remove"* ]] || [[ "$lowercase_msg" == *"delete"* ]] || [[ "$lowercase_msg" == *"deprecate"* ]]; then
            category="Removed"
        elif [[ "$lowercase_msg" == *"change"* ]] || [[ "$lowercase_msg" == *"update"* ]] || [[ "$lowercase_msg" == *"improve"* ]] || [[ "$lowercase_msg" == *"refactor"* ]]; then
            category="Changed"
        else
            category="Changed"
        fi
    fi
    
    echo "$category"
}

# Function to clean commit message
clean_message() {
    local message="$1"
    # Remove conventional commit prefix
    message=$(echo "$message" | sed -E 's/^(feat|fix|refactor|perf|chore|docs|style|test|build|ci|revert|add|remove|change|improve|update|bugfix|deprecate)(\([^)]+\))?:\s*//i')
    # Remove leading/trailing whitespace
    message=$(echo "$message" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    # Capitalize first letter
    message=$(echo "$message" | sed 's/./\u&/')
    echo "$message"
}

# Function to get commits for a range
get_commits_by_category() {
    local range="$1"
    local category="$2"
    local commits=""
    
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            msg=$(categorize_commit "$line")
            if [ "$msg" = "$category" ]; then
                commits="$commits$line\n"
            fi
        fi
    done < <(git log --pretty=format:"%s" "$range" 2>/dev/null || echo "")
    
    echo -e "$commits" | grep -v '^$' | sort -u
}

# Function to generate changelog for a version
generate_version_section() {
    local version="$1"
    local range="$2"
    local date="$3"
    
    echo "## [$version]$date"
    echo ""
    
    local has_content=false
    
    for category in "Added" "Fixed" "Changed" "Removed" "Documentation"; do
        local commits
        commits=$(get_commits_by_category "$range" "$category")
        
        if [ -n "$commits" ]; then
            has_content=true
            echo "### $category"
            while IFS= read -r commit; do
                if [ -n "$commit" ]; then
                    local cleaned
                    cleaned=$(clean_message "$commit")
                    echo "- $cleaned"
                fi
            done <<< "$commits"
            echo ""
        fi
    done
    
    if [ "$has_content" = false ]; then
        echo "_No changes documented._"
        echo ""
    fi
}

# Start generating the changelog
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    echo ""
    
    # Generate Unreleased section
    if [ -n "$LATEST_TAG" ]; then
        generate_version_section "Unreleased" "$LATEST_TAG..HEAD" ""
    fi
    
    # Generate sections for each tag
    prev_tag=""
    first_tag=true
    
    for tag in $TAGS; do
        if [ "$first_tag" = true ]; then
            # First tag: get all commits up to this tag
            range="$tag"
            first_tag=false
        else
            # Get commits between previous tag and this tag
            range="$prev_tag..$tag"
        fi
        
        # Get tag date
        tag_date=$(git log -1 --format="%ai" "$tag" 2>/dev/null | cut -d' ' -f1 || echo "")
        if [ -n "$tag_date" ]; then
            date_str=" - $tag_date"
        else
            date_str=""
        fi
        
        # Clean tag name (remove 'v' prefix if present)
        version=$(echo "$tag" | sed 's/^v//')
        
        generate_version_section "$version" "$range" "$date_str"
        
        prev_tag="$tag"
    done
    
    # If no tags, generate from all commits
    if [ -z "$TAGS" ]; then
        generate_version_section "Unreleased" "HEAD" ""
    fi
    
} > "$OUTPUT_FILE"

echo "✅ Generated $OUTPUT_FILE"
echo ""
echo "Next steps:"
echo "1. Review the generated changelog"
echo "2. Edit as needed for clarity"
echo "3. Commit: git add $OUTPUT_FILE && git commit -m 'docs: update CHANGELOG'"