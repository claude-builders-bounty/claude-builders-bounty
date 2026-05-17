#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [repo_path] [--tag TAG] [--output FILE]
#   repo_path   : Path to the git repo (default: current directory)
#   --tag TAG   : Generate changelog since this tag (default: last tag)
#   --output FILE: Output file (default: CHANGELOG.md)

set -euo pipefail

REPO_PATH="."
SINCE_TAG=""
OUTPUT_FILE="CHANGELOG.md"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --tag)    SINCE_TAG="$2"; shift 2 ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
        -*)       echo "Unknown option: $1" >&2; exit 1 ;;
        *)        REPO_PATH="$1"; shift ;;
    esac
done

cd "$REPO_PATH"

# Verify we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Error: Not a git repository: $REPO_PATH" >&2
    exit 1
fi

# Determine the last tag if not specified
if [[ -z "$SINCE_TAG" ]]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -z "$SINCE_TAG" ]]; then
        echo "No tags found. Generating changelog from the beginning of history."
        SINCE_REV=""
    else
        echo "Last tag found: $SINCE_TAG"
        SINCE_REV="$SINCE_TAG"
    fi
else
    SINCE_REV="$SINCE_TAG"
fi

# Get the current version
NEXT_VERSION=$(git describe --tags --always --dirty 2>/dev/null)
CURRENT_DATE=$(date +%Y-%m-%d)

# Fetch commit subjects since the tag
if [[ -n "$SINCE_REV" ]]; then
    COMMITS=$(git log "${SINCE_REV}..HEAD" --pretty=format:"%s" --no-merges 2>/dev/null)
else
    COMMITS=$(git log --pretty=format:"%s" --no-merges 2>/dev/null)
fi

if [[ -z "$COMMITS" ]]; then
    echo "No new commits found since ${SINCE_TAG:-start}"
    exit 0
fi

# Categorize commits by subject prefix
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

strip_prefix() {
    # Strip conventional-commit-style prefix: "type(scope): message" → "message"
    echo "$1" | sed -E 's/^[a-z]+(\(.+\))?:\s*//i'
}

while IFS= read -r subject; do
    [[ -z "$subject" ]] && continue
    lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

    if echo "$lower" | grep -qE '^(add|feat|feature|new|create|implement|introduce|support)\b'; then
        ADDED+=("$(strip_prefix "$subject")")
    elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|hotfix|repair|correct)\b'; then
        FIXED+=("$(strip_prefix "$subject")")
    elif echo "$lower" | grep -qE '^(change|update|refactor|improve|rename|move|migrate|bump|upgrade|downgrade|replace|modify|revert)\b'; then
        CHANGED+=("$(strip_prefix "$subject")")
    elif echo "$lower" | grep -qE '^(remove|delete|drop|deprecate|strip|eliminate)\b'; then
        REMOVED+=("$(strip_prefix "$subject")")
    else
        OTHER+=("$(strip_prefix "$subject")")
    fi
done <<< "$COMMITS"

# Generate CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$NEXT_VERSION] - $CURRENT_DATE"
    echo ""

    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        echo ""
        for entry in "${ADDED[@]}"; do echo "- $entry"; done
        echo ""
    fi

    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        echo ""
        for entry in "${FIXED[@]}"; do echo "- $entry"; done
        echo ""
    fi

    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        echo ""
        for entry in "${CHANGED[@]}"; do echo "- $entry"; done
        echo ""
    fi

    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        echo ""
        for entry in "${REMOVED[@]}"; do echo "- $entry"; done
        echo ""
    fi

    if [[ ${#OTHER[@]} -gt 0 ]]; then
        echo "### Other"
        echo ""
        for entry in "${OTHER[@]}"; do echo "- $entry"; done
        echo ""
    fi

    # Add comparison links if we have tags and remote
    if [[ -n "$SINCE_TAG" ]]; then
        REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
        if [[ -n "$REMOTE_URL" ]]; then
            REMOTE_URL=$(echo "$REMOTE_URL" | sed -E 's/\.git$//' | sed -E 's|git@([^:]+):|https://\1/|')
            echo "[$NEXT_VERSION]: ${REMOTE_URL}/compare/${SINCE_TAG}...${NEXT_VERSION}"
        fi
    fi
} > "$OUTPUT_FILE"

COMMIT_COUNT=$(echo "$COMMITS" | wc -l | tr -d ' ')
echo "✅ Generated $OUTPUT_FILE with $COMMIT_COUNT commits since ${SINCE_TAG:-start}"
echo "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]} | Other: ${#OTHER[@]}"
