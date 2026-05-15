#!/usr/bin/env bash
# changelog.sh — generates CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <ref>] [--output <file>]
set -eo pipefail

OUTPUT="CHANGELOG.md"
SINCE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --since) SINCE="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

# Ensure we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "ERROR: Not a git repository." >&2
    exit 1
fi

# Determine the range: from last tag to HEAD
if [[ -z "$SINCE" ]]; then
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
    if [[ -n "$LAST_TAG" ]]; then
        RANGE="${LAST_TAG}..HEAD"
        SINCE_LABEL="since tag ${LAST_TAG}"
    else
        RANGE="HEAD"
        SINCE_LABEL="all commits (no tags found)"
    fi
else
    RANGE="${SINCE}..HEAD"
    SINCE_LABEL="since ${SINCE}"
fi

echo "Collecting commits ${SINCE_LABEL}..." >&2

# Collect commits: hash | subject
mapfile -t COMMITS < <(git log "$RANGE" --pretty=format:"%h|%s" --no-merges 2>/dev/null || git log --pretty=format:"%h|%s" --no-merges)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
    echo "No commits found ${SINCE_LABEL}." >&2
    exit 0
fi

# Category buckets
declare -a ADDED FIXED CHANGED REMOVED UNCATEGORIZED

classify() {
    local subject="$1"
    local lower="${subject,,}"

    # Conventional commits prefix parsing
    local prefix="${lower%%:*}"

    case "$prefix" in
        feat|feature|add|new) echo "added" ;;
        fix|bugfix|hotfix|patch) echo "fixed" ;;
        refactor|perf|style|chore|ci|build|test|docs|doc|update|change|improve|enhance) echo "changed" ;;
        remove|delete|drop|revert|deprecate) echo "removed" ;;
        *)
            # Fallback: keyword search in subject
            if [[ "$lower" =~ ^(add|new |feature|implement|creat|introduc) ]]; then echo "added"
            elif [[ "$lower" =~ (fix|bug|patch|resolv|repair|correct|error|fail|broken) ]]; then echo "fixed"
            elif [[ "$lower" =~ (remov|delet|drop|revert|deprecat) ]]; then echo "removed"
            else echo "changed"
            fi
            ;;
    esac
}

for entry in "${COMMITS[@]}"; do
    hash="${entry%%|*}"
    subject="${entry#*|}"
    category=$(classify "$subject")
    line="- ${subject} (\`${hash}\`)"
    case "$category" in
        added)   ADDED+=("$line") ;;
        fixed)   FIXED+=("$line") ;;
        removed) REMOVED+=("$line") ;;
        *)       CHANGED+=("$line") ;;
    esac
done

# Write CHANGELOG.md
TODAY=$(date +%Y-%m-%d)
NEXT_VERSION="Unreleased"

# Read existing tagged sections BEFORE overwriting the file
EXISTING_SECTIONS=""
if [[ -f "$OUTPUT" ]]; then
    EXISTING_SECTIONS=$(awk '/^## \[/{c++} c>=2{print}' "$OUTPUT")
fi

{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo "Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)."
    echo ""
    echo "## [${NEXT_VERSION}] — ${TODAY}"
    echo ""

    if [[ ${#ADDED[@]} -gt 0 ]]; then
        echo "### Added"
        printf '%s\n' "${ADDED[@]+"${ADDED[@]}"}"
        echo ""
    fi

    if [[ ${#CHANGED[@]} -gt 0 ]]; then
        echo "### Changed"
        printf '%s\n' "${CHANGED[@]+"${CHANGED[@]}"}"
        echo ""
    fi

    if [[ ${#FIXED[@]} -gt 0 ]]; then
        echo "### Fixed"
        printf '%s\n' "${FIXED[@]+"${FIXED[@]}"}"
        echo ""
    fi

    if [[ ${#REMOVED[@]} -gt 0 ]]; then
        echo "### Removed"
        printf '%s\n' "${REMOVED[@]+"${REMOVED[@]}"}"
        echo ""
    fi

    if [[ -n "$EXISTING_SECTIONS" ]]; then
        echo "$EXISTING_SECTIONS"
    fi
} > "$OUTPUT"

echo "✓ CHANGELOG.md written (${#COMMITS[@]} commits, ${SINCE_LABEL})" >&2
echo "  Added: ${#ADDED[@]}  Changed: ${#CHANGED[@]}  Fixed: ${#FIXED[@]}  Removed: ${#REMOVED[@]}" >&2
cat "$OUTPUT"
