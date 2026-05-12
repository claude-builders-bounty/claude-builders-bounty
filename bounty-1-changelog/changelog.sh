#!/usr/bin/env bash
#
# changelog.sh - Generate a structured CHANGELOG.md from git history
#
# Usage: bash changelog.sh [output_file]
#
# Fetches commits since the last git tag (or all commits if no tags exist),
# categorizes them by conventional commit prefixes or keyword heuristics,
# and outputs a formatted CHANGELOG.md.

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
TODAY=$(date +%Y-%m-%d)

# ---------------------------------------------------------------------------
# Determine version range
# ---------------------------------------------------------------------------

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [[ -n "$LAST_TAG" ]]; then
    echo "Last tag: $LAST_TAG"
    COMMIT_RANGE="${LAST_TAG}..HEAD"

    # Attempt to compute next patch version from semver tag
    if [[ "$LAST_TAG" =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
        PREFIX=""
        [[ "$LAST_TAG" == v* ]] && PREFIX="v"
        MAJOR="${BASH_REMATCH[1]}"
        MINOR="${BASH_REMATCH[2]}"
        PATCH="${BASH_REMATCH[3]}"
        NEXT_VERSION="${PREFIX}${MAJOR}.${MINOR}.$((PATCH + 1))"
    else
        NEXT_VERSION="Unreleased"
    fi
else
    echo "No tags found. Using entire commit history."
    COMMIT_RANGE=""
    NEXT_VERSION="Unreleased"
fi

echo "Version: $NEXT_VERSION"
echo "Date: $TODAY"
echo ""

# ---------------------------------------------------------------------------
# Fetch commits
# ---------------------------------------------------------------------------

if [[ -n "$COMMIT_RANGE" ]]; then
    COMMITS=$(git log "$COMMIT_RANGE" --pretty=format:"%h|||%s" --no-merges 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%h|||%s" --no-merges 2>/dev/null || echo "")
fi

if [[ -z "$COMMITS" ]]; then
    echo "No commits found. Nothing to generate."
    exit 0
fi

# ---------------------------------------------------------------------------
# Categorize commits
# ---------------------------------------------------------------------------

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

categorize_commit() {
    local hash="$1"
    local message="$2"
    local display_message="$message"
    local category=""

    # Check for conventional commit prefix (word before first colon)
    if [[ "$message" =~ ^([a-zA-Z]+)(\(.*\))?:\ *(.*) ]]; then
        local prefix
        prefix=$(echo "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')
        display_message="${BASH_REMATCH[3]}"

        case "$prefix" in
            feat|feature|add)
                category="added" ;;
            fix|bugfix|hotfix)
                category="fixed" ;;
            remove|delete|deprecate)
                category="removed" ;;
            refactor|change|update|improve|perf|style|chore|build|ci|docs|test|revert|breaking)
                category="changed" ;;
        esac
    fi

    # Fallback: keyword heuristics
    if [[ -z "$category" ]]; then
        local lower
        lower=$(echo "$message" | tr '[:upper:]' '[:lower:]')
        if [[ "$lower" =~ (^|[^a-z])(add|new|create|introduce|implement|support)([^a-z]|$) ]]; then
            category="added"
        elif [[ "$lower" =~ (^|[^a-z])(fix|bug|patch|resolve|correct|repair)([^a-z]|$) ]]; then
            category="fixed"
        elif [[ "$lower" =~ (^|[^a-z])(remove|delete|drop|deprecate|strip)([^a-z]|$) ]]; then
            category="removed"
        elif [[ "$lower" =~ (^|[^a-z])(update|change|modify|refactor|improve|enhance|rename|move|migrate|upgrade|adjust|optimize)([^a-z]|$) ]]; then
            category="changed"
        else
            category="changed"
        fi
    fi

    # Capitalize first letter of display message
    display_message="$(echo "${display_message:0:1}" | tr '[:lower:]' '[:upper:]')${display_message:1}"

    local entry="- ${display_message} (${hash})"

    case "$category" in
        added)   ADDED+=("$entry") ;;
        fixed)   FIXED+=("$entry") ;;
        removed) REMOVED+=("$entry") ;;
        *)       CHANGED+=("$entry") ;;
    esac
}

while IFS= read -r line; do
    hash="${line%%|||*}"
    message="${line#*|||}"
    categorize_commit "$hash" "$message"
done <<< "$COMMITS"

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))

echo "Commits processed: $TOTAL"
echo "  Added:   ${#ADDED[@]}"
echo "  Fixed:   ${#FIXED[@]}"
echo "  Changed: ${#CHANGED[@]}"
echo "  Removed: ${#REMOVED[@]}"
echo ""

# ---------------------------------------------------------------------------
# Build the changelog content
# ---------------------------------------------------------------------------

HEADER="# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."

NEW_SECTION="## [$NEXT_VERSION] - $TODAY"

if [[ ${#ADDED[@]} -gt 0 ]]; then
    NEW_SECTION+=$'\n\n### Added'
    for entry in "${ADDED[@]}"; do
        NEW_SECTION+=$'\n'"$entry"
    done
fi

if [[ ${#FIXED[@]} -gt 0 ]]; then
    NEW_SECTION+=$'\n\n### Fixed'
    for entry in "${FIXED[@]}"; do
        NEW_SECTION+=$'\n'"$entry"
    done
fi

if [[ ${#CHANGED[@]} -gt 0 ]]; then
    NEW_SECTION+=$'\n\n### Changed'
    for entry in "${CHANGED[@]}"; do
        NEW_SECTION+=$'\n'"$entry"
    done
fi

if [[ ${#REMOVED[@]} -gt 0 ]]; then
    NEW_SECTION+=$'\n\n### Removed'
    for entry in "${REMOVED[@]}"; do
        NEW_SECTION+=$'\n'"$entry"
    done
fi

# ---------------------------------------------------------------------------
# Write output (preserve existing content if present)
# ---------------------------------------------------------------------------

if [[ -f "$OUTPUT_FILE" ]]; then
    # Extract existing entries (everything after the header block)
    EXISTING=$(sed -n '/^## \[/,$p' "$OUTPUT_FILE")
    if [[ -n "$EXISTING" ]]; then
        FINAL_CONTENT="${HEADER}"$'\n\n'"${NEW_SECTION}"$'\n\n'"${EXISTING}"
    else
        FINAL_CONTENT="${HEADER}"$'\n\n'"${NEW_SECTION}"
    fi
else
    FINAL_CONTENT="${HEADER}"$'\n\n'"${NEW_SECTION}"
fi

echo "$FINAL_CONTENT" > "$OUTPUT_FILE"

echo "Changelog written to: $OUTPUT_FILE"
