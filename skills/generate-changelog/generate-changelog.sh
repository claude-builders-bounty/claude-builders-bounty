#!/bin/bash

# CHANGELOG Generator from Git History
# Usage: ./generate-changelog.sh [--output CHANGELOG.md]

set -e

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_NAME=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[\/:]\(.*\)\.git/\1/' || echo "local/repo")
REPO_URL="https://github.com/$REPO_NAME"

echo "# Changelog" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "> All notable changes to this project will be documented in this file." >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)," >> "$OUTPUT_FILE"
echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)." >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Get all tags sorted by version (descending)
TAGS=$(git tag --sort=-v:refname 2>/dev/null || echo "")

# Function to categorize commit
categorize_commit() {
    local message="$1"
    local category="other"
    
    if [[ "$message" =~ ^feat ]] || [[ "$message" =~ ^feature ]]; then
        category="Added"
    elif [[ "$message" =~ ^fix ]]; then
        category="Fixed"
    elif [[ "$message" =~ ^docs ]]; then
        category="Documentation"
    elif [[ "$message" =~ ^style ]]; then
        category="Changed"
    elif [[ "$message" =~ ^refactor ]]; then
        category="Changed"
    elif [[ "$message" =~ ^perf ]]; then
        category="Performance"
    elif [[ "$message" =~ ^test ]]; then
        category="Testing"
    elif [[ "$message" =~ ^build ]]; then
        category="Build"
    elif [[ "$message" =~ ^ci ]]; then
        category="CI/CD"
    elif [[ "$message" =~ ^chore ]]; then
        category="Maintenance"
    fi
    
    echo "$category"
}

# Function to format commit for changelog
format_commit() {
    local hash="$1"
    local message="$2"
    local category="$3"
    
    # Remove conventional commit prefix
    local clean_message=$(echo "$message" | sed -E 's/^(feat|feature|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?:\s*//')
    
    # Capitalize first letter
    clean_message=$(echo "$clean_message" | sed 's/^\(.\)/\U\1/')
    
    echo "- $clean_message ([\`${hash:0:7}\`]($REPO_URL/commit/$hash))"
}

# Process unreleased commits (if no tags, all commits are unreleased)
if [ -z "$TAGS" ]; then
    echo "## [Unreleased]" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    
    COMMITS=$(git log --pretty=format:"%H|%s" --no-merges 2>/dev/null || echo "")
    
    if [ -n "$COMMITS" ]; then
        declare -A CATEGORIES
        
        while IFS='|' read -r hash message; do
            category=$(categorize_commit "$message")
            CATEGORIES["$category"]+="$hash|$message"$'\n'
        done <<< "$COMMITS"
        
        for category in "Added" "Changed" "Fixed" "Documentation" "Performance" "Testing" "Build" "CI/CD" "Maintenance" "other"; do
            if [ -n "${CATEGORIES[$category]}" ]; then
                echo "### $category" >> "$OUTPUT_FILE"
                while IFS='|' read -r hash message; do
                    [ -n "$hash" ] && format_commit "$hash" "$message" "$category" >> "$OUTPUT_FILE"
                done <<< "${CATEGORIES[$category]}"
                echo "" >> "$OUTPUT_FILE"
            fi
        done
    fi
else
    # Process unreleased commits (commits after the latest tag)
    LATEST_TAG=$(echo "$TAGS" | head -1)
    UNRELEASED=$(git log --pretty=format:"%H|%s" --no-merges $LATEST_TAG..HEAD 2>/dev/null || echo "")
    
    if [ -n "$UNRELEASED" ]; then
        echo "## [Unreleased]" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        declare -A CATEGORIES
        
        while IFS='|' read -r hash message; do
            category=$(categorize_commit "$message")
            CATEGORIES["$category"]+="$hash|$message"$'\n'
        done <<< "$UNRELEASED"
        
        for category in "Added" "Changed" "Fixed" "Documentation" "Performance" "Testing" "Build" "CI/CD" "Maintenance" "other"; do
            if [ -n "${CATEGORIES[$category]}" ]; then
                echo "### $category" >> "$OUTPUT_FILE"
                while IFS='|' read -r hash message; do
                    [ -n "$hash" ] && format_commit "$hash" "$message" "$category" >> "$OUTPUT_FILE"
                done <<< "${CATEGORIES[$category]}"
                echo "" >> "$OUTPUT_FILE"
            fi
        done
    fi
    
    # Process each tagged version
    PREV_TAG=""
    FIRST_TAG=true
    
    for TAG in $TAGS; do
        TAG_DATE=$(git log -1 --format=%ai $TAG 2>/dev/null | cut -d' ' -f1 || echo "Unknown")
        TAG_MESSAGE=$(git tag -l "$TAG" --format='%(contents:subject)' 2>/dev/null || echo "")
        
        # Clean tag name (remove 'v' prefix if present)
        VERSION=$(echo "$TAG" | sed 's/^v//')
        
        echo "## [$VERSION] - $TAG_DATE" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        
        # Get commits for this version
        if [ -n "$PREV_TAG" ]; then
            COMMITS=$(git log --pretty=format:"%H|%s" --no-merges $PREV_TAG..$TAG 2>/dev/null || echo "")
        else
            COMMITS=$(git log --pretty=format:"%H|%s" --no-merges $TAG 2>/dev/null || echo "")
        fi
        
        if [ -n "$COMMITS" ]; then
            declare -A CATEGORIES
            
            while IFS='|' read -r hash message; do
                category=$(categorize_commit "$message")
                CATEGORIES["$category"]+="$hash|$message"$'\n'
            done <<< "$COMMITS"
            
            for category in "Added" "Changed" "Fixed" "Documentation" "Performance" "Testing" "Build" "CI/CD" "Maintenance" "other"; do
                if [ -n "${CATEGORIES[$category]}" ]; then
                    echo "### $category" >> "$OUTPUT_FILE"
                    while IFS='|' read -r hash message; do
                        [ -n "$hash" ] && format_commit "$hash" "$message" "$category" >> "$OUTPUT_FILE"
                    done <<< "${CATEGORIES[$category]}"
                    echo "" >> "$OUTPUT_FILE"
                fi
            done
        fi
        
        PREV_TAG=$TAG
    done
fi

# Add links section
echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "[Unreleased]: $REPO_URL/compare/HEAD..HEAD" >> "$OUTPUT_FILE"

# Add version comparison links
PREV_TAG=""
for TAG in $TAGS; do
    VERSION=$(echo "$TAG" | sed 's/^v//')
    
    if [ -n "$PREV_TAG" ]; then
        PREV_VERSION=$(echo "$PREV_TAG" | sed 's/^v//')
        echo "[$VERSION]: $REPO_URL/compare/$PREV_TAG..$TAG" >> "$OUTPUT_FILE"
    else
        echo "[$VERSION]: $REPO_URL/releases/tag/$TAG" >> "$OUTPUT_FILE"
    fi
    
    PREV_TAG=$TAG
done

echo "" >> "$OUTPUT_FILE"
echo "---" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "_Generated by [generate-changelog](https://github.com/ljapptest-art/generate-changelog)_" >> "$OUTPUT_FILE"

echo "✅ CHANGELOG generated: $OUTPUT_FILE"
