#!/usr/bin/env bash
#
# changelog.sh
# Generates a beautifully formatted CHANGELOG.md from git history.
#

set -euo pipefail

# 1. Verify we are in a Git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not a Git repository." >&2
    exit 1
fi

# 2. Get the latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LATEST_TAG" ]; then
    echo "Latest tag found: $LATEST_TAG. Fetching commits since $LATEST_TAG..."
    REVISION_RANGE="$LATEST_TAG..HEAD"
else
    echo "No tags found in the repository. Fetching all commits..."
    REVISION_RANGE="HEAD"
fi

# 3. Get remote repository path for proper commit links
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
REPO_PATH=$(echo "$REMOTE_URL" | sed -E -e 's/git@github.com://' -e 's/https:\/\/github.com\///' -e 's/\.git$//' -e 's/ssh:\/\/git@github.com\///')
if [ -n "$REPO_PATH" ]; then
    GH_URL_PREFIX="https://github.com/$REPO_PATH/commit"
else
    GH_URL_PREFIX=""
fi

# 4. Initialize arrays for categorization
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

# 5. Fetch commits with format: [hash] | [date] | [author] | [subject]
# Using %h for abbreviated commit hash, %cs for committer date (YYYY-MM-DD), %an for author name, %s for subject
while IFS='|' read -r commit_hash commit_date commit_author commit_subject; do
    # Trim leading/trailing whitespace
    commit_subject=$(echo "$commit_subject" | xargs)
    commit_author=$(echo "$commit_author" | xargs)
    commit_date=$(echo "$commit_date" | xargs)
    commit_hash=$(echo "$commit_hash" | xargs)
    
    # Skip empty entries
    if [ -z "$commit_subject" ]; then
        continue
    fi
    
    # Format line with GitHub commit link if possible
    if [ -n "$GH_URL_PREFIX" ]; then
        ENTRY="- **$commit_subject** ([$commit_hash]($GH_URL_PREFIX/$commit_hash) by $commit_author on $commit_date)"
    else
        ENTRY="- **$commit_subject** ($commit_hash by $commit_author on $commit_date)"
    fi
    
    # Auto-categorization based on subject prefixes (case-insensitive)
    SUBJECT_LOWER=$(echo "$commit_subject" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$SUBJECT_LOWER" =~ ^(feat|add|new|implement|feature) ]]; then
        ADDED+=("$ENTRY")
    elif [[ "$SUBJECT_LOWER" =~ ^(fix|bug|resolve|patch) ]]; then
        FIXED+=("$ENTRY")
    elif [[ "$SUBJECT_LOWER" =~ ^(remove|delete|deprecate) ]]; then
        REMOVED+=("$ENTRY")
    else
        # Default category is Changed (refactor, perf, docs, style, chore, clean, etc.)
        CHANGED+=("$ENTRY")
    fi
done < <(git log "$REVISION_RANGE" --pretty=format:"%h|%cs|%an|%s" --no-merges)

# 6. Build CHANGELOG.md
OUTPUT_FILE="CHANGELOG.md"
echo "Generating $OUTPUT_FILE..."

{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    
    # Added
    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "## 🚀 Added"
        echo ""
        for entry in "${ADDED[@]}"; do
            echo "$entry"
        done
        echo ""
    fi
    
    # Fixed
    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "## 🐛 Fixed"
        echo ""
        for entry in "${FIXED[@]}"; do
            echo "$entry"
        done
        echo ""
    fi
    
    # Changed
    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "## ⚙️ Changed"
        echo ""
        for entry in "${CHANGED[@]}"; do
            echo "$entry"
        done
        echo ""
    fi
    
    # Removed
    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "## 🗑️ Removed"
        echo ""
        for entry in "${REMOVED[@]}"; do
            echo "$entry"
        done
        echo ""
    fi
    
    # If all buckets are empty
    if [ ${#ADDED[@]} -eq 0 ] && [ ${#FIXED[@]} -eq 0 ] && [ ${#CHANGED[@]} -eq 0 ] && [ ${#REMOVED[@]} -eq 0 ]; then
        echo "_No changes since last release._"
        echo ""
    fi
    
    echo "---"
    echo "*Generated automatically by Git Changelog Generator on $(date +%Y-%m-%d)*"
} > "$OUTPUT_FILE"

echo "Changelog successfully generated at $OUTPUT_FILE! 🎉"
