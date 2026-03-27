#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh [output-file]
#
# Arguments:
#   output-file   Path to write the changelog (default: CHANGELOG.md)
#
# Categorizes commits using conventional commit prefixes (feat:, fix:, etc.)
# with keyword-based fallback. Fetches commits since the last git tag.
#
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
DATE=$(date +%Y-%m-%d)

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Error: not inside a git repository." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Find latest tag
# ---------------------------------------------------------------------------

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -n "$LAST_TAG" ]; then
    echo "Generating changelog for commits since tag: $LAST_TAG"
else
    echo "No tags found. Generating changelog from all commits."
fi

# ---------------------------------------------------------------------------
# Fetch commits
# ---------------------------------------------------------------------------

fetch_commits() {
    local fmt='%h%x09%s'
    if [ -n "$LAST_TAG" ]; then
        git log "${LAST_TAG}..HEAD" --pretty=format:"$fmt" --no-merges
    else
        git log --pretty=format:"$fmt" --no-merges
    fi
}

# ---------------------------------------------------------------------------
# Categorize
# ---------------------------------------------------------------------------

added=()
fixed=()
changed=()
removed=()

while IFS=$'\t' read -r hash subject || [ -n "$hash" ]; do
    [ -z "$hash" ] && continue

    lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

    # Extract conventional commit type: feat, fix, chore, etc.
    type=$(echo "$lower" | sed -nE 's/^([a-z]+)(\([^)]*\))?!?:[[:space:]].*/\1/p')

    # Strip conventional commit prefix for clean display
    clean=$(echo "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')
    [ -z "$clean" ] && clean="$subject"

    # Capitalize first letter (portable across macOS + Linux)
    first_char=$(echo "$clean" | cut -c1 | tr '[:lower:]' '[:upper:]')
    rest=$(echo "$clean" | cut -c2-)
    clean="${first_char}${rest}"

    entry="- ${clean} (\`${hash}\`)"

    # Categorize by conventional commit type
    case "$type" in
        feat|add|new)
            added+=("$entry") ;;
        fix|bugfix|patch|hotfix)
            fixed+=("$entry") ;;
        remove|delete|drop|deprecate|revert)
            removed+=("$entry") ;;
        refactor|update|improve|perf|style|enhance|chore|ci|build|docs|test)
            changed+=("$entry") ;;
        *)
            # Keyword-based fallback for non-conventional commits
            case "$lower" in
                *add*|*new\ *|*creat*|*introduc*|*implement*|*support*|*enabl*)
                    added+=("$entry") ;;
                *fix*|*resolv*|*repair*|*patch*|*correct*)
                    fixed+=("$entry") ;;
                *remov*|*delet*|*drop*|*deprecat*|*revert*|*strip*)
                    removed+=("$entry") ;;
                *)
                    changed+=("$entry") ;;
            esac
            ;;
    esac
done < <(fetch_commits)

# ---------------------------------------------------------------------------
# Check for empty result
# ---------------------------------------------------------------------------

total=$(( ${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]} ))

if [ "$total" -eq 0 ]; then
    echo "No new commits found${LAST_TAG:+ since $LAST_TAG}. Nothing to generate."
    exit 0
fi

# ---------------------------------------------------------------------------
# Build section header
# ---------------------------------------------------------------------------

if [ -n "$LAST_TAG" ]; then
    header="## [Unreleased] (since ${LAST_TAG}) — ${DATE}"
else
    header="## [Unreleased] — ${DATE}"
fi

# ---------------------------------------------------------------------------
# Write CHANGELOG.md
# ---------------------------------------------------------------------------

{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
    echo ""
    echo "$header"
    echo ""

    if [ ${#added[@]} -gt 0 ]; then
        echo "### Added"
        echo ""
        printf '%s\n' "${added[@]}"
        echo ""
    fi

    if [ ${#fixed[@]} -gt 0 ]; then
        echo "### Fixed"
        echo ""
        printf '%s\n' "${fixed[@]}"
        echo ""
    fi

    if [ ${#changed[@]} -gt 0 ]; then
        echo "### Changed"
        echo ""
        printf '%s\n' "${changed[@]}"
        echo ""
    fi

    if [ ${#removed[@]} -gt 0 ]; then
        echo "### Removed"
        echo ""
        printf '%s\n' "${removed[@]}"
        echo ""
    fi
} > "$OUTPUT"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "✓ Changelog written to ${OUTPUT}"
echo "  Added: ${#added[@]} | Fixed: ${#fixed[@]} | Changed: ${#changed[@]} | Removed: ${#removed[@]}"
