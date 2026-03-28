#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh                 # Generate since last tag
#   bash changelog.sh v1.0.0          # Generate since specific tag
#   bash changelog.sh --all           # Generate from all history

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG="${1:-}"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
DATE=$(date +%Y-%m-%d)

# --- Determine version range ---

if [[ "$SINCE_TAG" == "--all" ]]; then
    RANGE=""
    VERSION_LABEL="Full History"
elif [[ -n "$SINCE_TAG" ]]; then
    RANGE="${SINCE_TAG}..HEAD"
    VERSION_LABEL="Changes since ${SINCE_TAG}"
else
    LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$LATEST_TAG" ]]; then
        RANGE="${LATEST_TAG}..HEAD"
        VERSION_LABEL="Changes since ${LATEST_TAG}"
    else
        RANGE=""
        VERSION_LABEL="All Changes"
    fi
fi

# --- Fetch commits ---

if [[ -n "$RANGE" ]]; then
    COMMITS=$(git log "$RANGE" --pretty=format:"%s" --no-merges 2>/dev/null || echo "")
else
    COMMITS=$(git log --pretty=format:"%s" --no-merges 2>/dev/null || echo "")
fi

if [[ -z "$COMMITS" ]]; then
    echo "No commits found. Nothing to generate."
    exit 0
fi

# --- Categorize commits ---

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r msg; do
    # Normalize: lowercase for matching, keep original for display
    lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

    # Clean conventional commit prefix for display
    display=$(echo "$msg" | sed -E 's/^(feat|fix|chore|docs|style|refactor|perf|test|build|ci|revert)(\([^)]*\))?[!]?:\s*//')

    if echo "$lower" | grep -qE '^(feat|add|new|create|implement|introduce)(\(|[!]?:|\s)'; then
        ADDED="${ADDED}- ${display}\n"
    elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|repair|correct)(\(|[!]?:|\s)'; then
        FIXED="${FIXED}- ${display}\n"
    elif echo "$lower" | grep -qE '(remove|delete|drop|deprecat|clean\s*up)'; then
        REMOVED="${REMOVED}- ${display}\n"
    elif echo "$lower" | grep -qE '^(refactor|change|update|improve|enhance|perf|optim|bump|chore|style|docs|build|ci|test)(\(|[!]?:|\s)'; then
        CHANGED="${CHANGED}- ${display}\n"
    else
        # Fallback heuristic based on keywords anywhere in message
        if echo "$lower" | grep -qE '(add|creat|new|implement|introduc|support)'; then
            ADDED="${ADDED}- ${display}\n"
        elif echo "$lower" | grep -qE '(fix|bug|patch|resolv|repair|correct)'; then
            FIXED="${FIXED}- ${display}\n"
        elif echo "$lower" | grep -qE '(chang|updat|improv|enhanc|refactor|modif|adjust|tweak)'; then
            CHANGED="${CHANGED}- ${display}\n"
        else
            OTHER="${OTHER}- ${display}\n"
        fi
    fi
done <<< "$COMMITS"

# --- Generate CHANGELOG.md ---

{
    echo "# Changelog"
    echo ""
    echo "## ${VERSION_LABEL} (${DATE})"
    echo ""

    if [[ -n "$ADDED" ]]; then
        echo "### Added"
        echo ""
        echo -e "$ADDED"
    fi

    if [[ -n "$FIXED" ]]; then
        echo "### Fixed"
        echo ""
        echo -e "$FIXED"
    fi

    if [[ -n "$CHANGED" ]]; then
        echo "### Changed"
        echo ""
        echo -e "$CHANGED"
    fi

    if [[ -n "$REMOVED" ]]; then
        echo "### Removed"
        echo ""
        echo -e "$REMOVED"
    fi

    if [[ -n "$OTHER" ]]; then
        echo "### Other"
        echo ""
        echo -e "$OTHER"
    fi
} > "$OUTPUT_FILE"

TOTAL=$(echo "$COMMITS" | wc -l | tr -d ' ')
echo "Generated ${OUTPUT_FILE} — ${TOTAL} commits categorized (${DATE})"
