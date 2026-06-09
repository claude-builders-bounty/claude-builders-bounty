#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Target output file
CHANGELOG_FILE="CHANGELOG.md"

echo "=== Claude Code Skill: Git Changelog Generator ==="

# 1. Get the last git tag
echo "Fetching last git tag..."
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Generating changelog from the beginning of git history..."
    COMMIT_RANGE="HEAD"
else
    echo "Last tag found: $LAST_TAG"
    COMMIT_RANGE="$LAST_TAG..HEAD"
fi

# Initialize lists
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

# 2. Read git history commits format: hash|subject
echo "Parsing commits..."
git log "$COMMIT_RANGE" --oneline --no-merges | while IFS= read -line commit; do
    # Extract commit hash and message
    HASH=$(echo "$commit" | cut -d' ' -f1)
    MSG=$(echo "$commit" | cut -d' ' -f2-)
    
    # Lowercase message for easier keyword matching
    LOWER_MSG=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')
    
    # Classify the commit based on conventional prefixes or keywords
    if [[ "$LOWER_MSG" =~ ^(feat|add|create|implement) ]] || [[ "$LOWER_MSG" =~ "add" ]]; then
        ADDED+=("* $MSG ([$HASH](https://github.com/\$REPO/commit/$HASH))")
    elif [[ "$LOWER_MSG" =~ ^(fix|bug|hotfix|resolve) ]] || [[ "$LOWER_MSG" =~ "fix" ]]; then
        FIXED+=("* $MSG ([$HASH](https://github.com/\$REPO/commit/$HASH))")
    elif [[ "$LOWER_MSG" =~ ^(remove|delete|deprecate) ]]; then
        REMOVED+=("* $MSG ([$HASH](https://github.com/\$REPO/commit/$HASH))")
    elif [[ "$LOWER_MSG" =~ ^(change|update|refactor|perf|docs|style) ]] || [[ "$LOWER_MSG" =~ "update" ]]; then
        CHANGED+=("* $MSG ([$HASH](https://github.com/\$REPO/commit/$HASH))")
    else
        OTHER+=("* $MSG ([$HASH](https://github.com/\$REPO/commit/$HASH))")
    fi
    
    # Save parsed categorized lists to temporary file as bash arrays don't survive while subshells
    echo "ADDED_LINE|* $MSG ([$HASH](https://github.com/\$REPO/commit/$HASH))" >> /tmp/changelog_tmp_data
done

# Initialize category files
echo "" > /tmp/added.txt
echo "" > /tmp/fixed.txt
echo "" > /tmp/changed.txt
echo "" > /tmp/removed.txt
echo "" > /tmp/other.txt

# Process temp lines to categories (workaround for subshell environment)
if [ -f /tmp/changelog_tmp_data ]; then
    # Get repository remote info to generate correct links
    REMOTE_URL=$(git config --get remote.origin.url || echo "origin")
    # Extract owner/repo
    if [[ "$REMOTE_URL" =~ github.com[:/]([^/]+/[^.]+)(.git)? ]]; then
        REPO="${BASH_REMATCH[1]}"
    else
        REPO="project/repo"
    fi

    while IFS= read -r line; do
        CAT=$(echo "$line" | cut -d'|' -f1)
        VAL=$(echo "$line" | cut -d'|' -f2- | sed "s|\\\$REPO|$REPO|g")
        
        # Categorize
        LOWER_VAL=$(echo "$VAL" | tr '[:upper:]' '[:lower:]')
        if [[ "$LOWER_VAL" =~ (feat|add|create|implement) ]] || [[ "$LOWER_VAL" =~ "add" ]]; then
            echo "$VAL" >> /tmp/added.txt
        elif [[ "$LOWER_VAL" =~ (fix|bug|hotfix|resolve) ]] || [[ "$LOWER_VAL" =~ "fix" ]]; then
            echo "$VAL" >> /tmp/fixed.txt
        elif [[ "$LOWER_VAL" =~ (remove|delete|deprecate) ]]; then
            echo "$VAL" >> /tmp/removed.txt
        elif [[ "$LOWER_VAL" =~ (change|update|refactor|perf|docs|style) ]] || [[ "$LOWER_VAL" =~ "update" ]]; then
            echo "$VAL" >> /tmp/changed.txt
        else
            echo "$VAL" >> /tmp/other.txt
        fi
    done < /tmp/changelog_tmp_data
    rm -f /tmp/changelog_tmp_data
fi

# 3. Build CHANGELOG.md
DATE=$(date +"%Y-%m-%d")
VERSION="[Unreleased]"
if [ ! -z "$LAST_TAG" ]; then
    VERSION="Next Version (after $LAST_TAG)"
fi

echo "Generating $CHANGELOG_FILE..."
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## $VERSION - $DATE"
    
    # Write Added
    if [ -s /tmp/added.txt ]; then
        echo ""
        echo "### Added"
        cat /tmp/added.txt | grep -v '^$'
    fi
    
    # Write Changed
    if [ -s /tmp/changed.txt ]; then
        echo ""
        echo "### Changed"
        cat /tmp/changed.txt | grep -v '^$'
    fi
    
    # Write Fixed
    if [ -s /tmp/fixed.txt ]; then
        echo ""
        echo "### Fixed"
        cat /tmp/fixed.txt | grep -v '^$'
    fi
    
    # Write Removed
    if [ -s /tmp/removed.txt ]; then
        echo ""
        echo "### Removed"
        cat /tmp/removed.txt | grep -v '^$'
    fi
    
    # Write Other
    if [ -s /tmp/other.txt ]; then
        echo ""
        echo "### Other / Miscellaneous"
        cat /tmp/other.txt | grep -v '^$'
    fi
    
} > "$CHANGELOG_FILE"

# Clean up temp files
rm -f /tmp/added.txt /tmp/fixed.txt /tmp/changed.txt /tmp/removed.txt /tmp/other.txt

echo "Changelog successfully generated: $CHANGELOG_FILE"
