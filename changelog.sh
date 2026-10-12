#!/bin/bash

# changelog.sh
#
# This script generates a structured CHANGELOG.md from git history.
# It fetches commits since the last git tag and categorizes them into
# 'Added', 'Fixed', 'Changed', and 'Removed' sections.

# --- Configuration ---
# Default output file
CHANGELOG_FILE="CHANGELOG.md"
# Default version for the new section if no tag is found or specified
DEFAULT_VERSION="Unreleased"
# GitHub repository URL prefix for commit links (e.g., "https://github.com/owner/repo/commit/")
# This will be automatically detected if possible, or can be set manually.
GITHUB_REPO_URL_PREFIX=""

# --- Helper Functions ---

# Function to get the latest git tag
get_latest_tag() {
    git describe --tags --abbrev=0 2>/dev/null
}

# Function to get the first commit hash
get_first_commit() {
    git rev-list --max-parents=0 HEAD
}

# Function to get the GitHub repository URL prefix
get_github_repo_url_prefix() {
    local remote_url=$(git config --get remote.origin.url 2>/dev/null)
    if [[ -z "$remote_url" ]]; then
        echo ""
        return
    fi

    # Handle common URL formats (HTTPS and SSH)
    if [[ "$remote_url" =~ ^https://github.com/([^/]+)/([^/]+)(\.git)?$ ]]; then
        echo "https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}/commit/"
    elif [[ "$remote_url" =~ ^git@github.com:([^/]+)/([^/]+)(\.git)?$ ]]; then
        echo "https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}/commit/"
    else
        echo ""
    fi
}

# --- Main Logic ---

echo "Generating CHANGELOG.md..."

# Detect GitHub repo URL prefix
GITHUB_REPO_URL_PREFIX=$(get_github_repo_url_prefix)

# Determine the commit range
LATEST_TAG=$(get_latest_tag)
if [[ -z "$LATEST_TAG" ]]; then
    echo "No git tags found. Generating changelog from the first commit to HEAD."
    COMMIT_RANGE="$(get_first_commit)..HEAD"
    CURRENT_VERSION="$DEFAULT_VERSION"
else
    echo "Latest tag found: $LATEST_TAG. Generating changelog from $LATEST_TAG to HEAD."
    COMMIT_RANGE="$LATEST_TAG..HEAD"
    # For a new release, we'd typically want to increment the version.
    # For simplicity, we'll just use "Unreleased" or prompt for a new version.
    # A more advanced script might try to parse and increment the tag version.
    CURRENT_VERSION="$DEFAULT_VERSION"
fi

# Prompt for a specific version if desired
read -p "Enter the version for this changelog section (default: $CURRENT_VERSION): " user_version
if [[ -n "$user_version" ]]; then
    CURRENT_VERSION="$user_version"
fi

# Fetch commits
# Format: %H (hash), %s (subject), %b (body)
# Using a custom delimiter for easier parsing
COMMIT_DELIMITER="---COMMIT-DELIMITER---"
COMMITS=$(git log --pretty=format:"%H%n%s%n%b%n$COMMIT_DELIMITER" "$COMMIT_RANGE")

# Initialize arrays for categorized commits
ADDED_COMMITS=()
FIXED_COMMITS=()
CHANGED_COMMITS=()
REMOVED_COMMITS=()

# Parse and categorize commits
IFS=$'\n' # Set Internal Field Separator to newline for loop
while IFS= read -r line; do
    if [[ "$line" == "$COMMIT_DELIMITER" ]]; then
        # Process the collected commit
        if [[ -n "$current_hash" && -n "$current_subject" ]]; then
            # Convert subject to lowercase for case-insensitive matching
            LOWER_SUBJECT=$(echo "$current_subject" | tr '[:upper:]' '[:lower:]')
            
            # Add commit link if GitHub URL prefix is available
            COMMIT_LINK=""
            if [[ -n "$GITHUB_REPO_URL_PREFIX" ]]; then
                COMMIT_LINK=" ([`echo $current_hash | cut -c1-7`]($GITHUB_REPO_URL_PREFIX$current_hash))"
            fi

            COMMIT_ENTRY="- $current_subject$COMMIT_LINK"

            # Categorization logic (order matters for some overlaps)
            if [[ "$LOWER_SUBJECT" =~ ^(feat|add|initial): ]]; then
                ADDED_COMMITS+=("$COMMIT_ENTRY")
            elif [[ "$LOWER_SUBJECT" =~ ^(fix|bug|patch): ]]; then
                FIXED_COMMITS+=("$COMMIT_ENTRY")
            elif [[ "$LOWER_SUBJECT" =~ ^(refactor|perf|style|docs|chore|build|ci|test|change|update|modify): ]]; then
                CHANGED_COMMITS+=("$COMMIT_ENTRY")
            elif [[ "$LOWER_SUBJECT" =~ ^(remove|deprecate): ]]; then
                REMOVED_COMMITS+=("$COMMIT_ENTRY")
            else
                # Default to Changed if no specific category
                CHANGED_COMMITS+=("$COMMIT_ENTRY")
            fi
        fi
        # Reset for the next commit
        current_hash=""
        current_subject=""
        current_body=""
        continue
    fi

    if [[ -z "$current_hash" ]]; then
        current_hash="$line"
    elif [[ -z "$current_subject" ]]; then
        current_subject="$line"
    else
        # Append to body
        current_body="$current_body"$'\n'"$line"
    fi
done <<< "$COMMITS"
unset IFS # Restore IFS

# Build the changelog content
CHANGELOG_CONTENT=""

# Add header for the new version
CHANGELOG_CONTENT+="# Changelog\n\n"
CHANGELOG_CONTENT+="## $CURRENT_VERSION\n"
CHANGELOG_CONTENT+="*Release Date: $(date +'%Y-%m-%d')*\n\n"

# Add categorized sections
if [[ ${#ADDED_COMMITS[@]} -gt 0 ]]; then
    CHANGELOG_CONTENT+="### Added\n"
    for entry in "${ADDED_COMMITS[@]}"; do
        CHANGELOG_CONTENT+="$entry\n"
    done
    CHANGELOG_CONTENT+="\n"
fi

if [[ ${#FIXED_COMMITS[@]} -gt 0 ]]; then
    CHANGELOG_CONTENT+="### Fixed\n"
    for entry in "${FIXED_COMMITS[@]}"; do
        CHANGELOG_CONTENT+="$entry\n"
    done
    CHANGELOG_CONTENT+="\n"
fi

if [[ ${#CHANGED_COMMITS[@]} -gt 0 ]]; then
    CHANGELOG_CONTENT+="### Changed\n"
    for entry in "${CHANGED_COMMITS[@]}"; do
        CHANGELOG_CONTENT+="$entry\n"
    done
    CHANGELOG_CONTENT+="\n"
fi

if [[ ${#REMOVED_COMMITS[@]} -gt 0 ]]; then
    CHANGELOG_CONTENT+="### Removed\n"
    for entry in "${REMOVED_COMMITS[@]}"; do
        CHANGELOG_CONTENT+="$entry\n"
    done
    CHANGELOG_CONTENT+="\n"
fi

# Prepend new content to existing CHANGELOG.md if it exists, otherwise create it.
if [[ -f "$CHANGELOG_FILE" ]]; then
    # Remove existing "Changelog" header if present to avoid duplicates
    EXISTING_CONTENT=$(cat "$CHANGELOG_FILE" | sed '/^# Changelog/d')
    echo -e "$CHANGELOG_CONTENT$EXISTING_CONTENT" > "$CHANGELOG_FILE"
else
    echo -e "$CHANGELOG_CONTENT" > "$CHANGELOG_FILE"
fi

echo "CHANGELOG.md generated successfully at $CHANGELOG_FILE"
echo "--- Sample Output ---"
head -n 20 "$CHANGELOG_FILE" # Show first 20 lines of the generated changelog
echo "---------------------"

