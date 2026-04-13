#!/usr/bin/env bash
#
# changelog.sh - Generate a structured CHANGELOG.md from git history
#
# Usage: bash changelog.sh [--output FILE] [--since TAG]
#
# Categories commits by conventional commit prefix:
#   feat:     -> Added
#   fix:      -> Fixed
#   refactor: -> Changed
#   change:   -> Changed
#   remove:   -> Removed
#   docs:     -> Changed
#   perf:     -> Changed
#   style:    -> Changed
#   chore:    -> Changed
#   *         -> Changed (default)

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --since|-s)
            SINCE_TAG="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: bash changelog.sh [--output FILE] [--since TAG]"
            echo ""
            echo "Options:"
            echo "  --output, -o FILE   Output file (default: CHANGELOG.md)"
            echo "  --since, -s TAG     Start from this tag (default: last tag or all commits)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Determine the range: since last tag, or all commits if no tags exist
if [[ -z "$SINCE_TAG" ]]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE_TAG" ]]; then
    RANGE="${SINCE_TAG}..HEAD"
    TITLE="Changes since ${SINCE_TAG}"
else
    RANGE="HEAD"
    TITLE="Changelog"
fi

# Collect commits
declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    hash="${line%% *}"
    msg="${line#* }"
    short_hash="${hash:0:7}"

    # Extract the conventional prefix (everything before the first colon)
    prefix=""
    rest="$msg"
    if [[ "$msg" =~ ^([a-zA-Z]+)(\(.+\))?!?:[[:space:]]*(.*) ]]; then
        prefix="${BASH_REMATCH[1],,}"  # lowercase
        rest="${BASH_REMATCH[3]}"
    fi

    # Capitalize first letter of description
    rest="${rest^}"

    entry="- ${rest} (\`${short_hash}\`)"

    case "$prefix" in
        feat)
            added+=("$entry")
            ;;
        fix)
            fixed+=("$entry")
            ;;
        refactor|change|chore|docs|perf|style|build|ci|test)
            changed+=("$entry")
            ;;
        remove|delete|revert)
            removed+=("$entry")
            ;;
        *)
            changed+=("$entry")
            ;;
    esac
done < <(git log --format="%H %s" "$RANGE" 2>/dev/null || git log --format="%H %s" 2>/dev/null)

# Get current date
DATE=$(date +%Y-%m-%d)

# Generate the changelog
{
    echo "# Changelog"
    echo ""
    echo "_${TITLE} — ${DATE}_"
    echo ""

    if [[ ${#added[@]} -gt 0 ]]; then
        echo "## Added"
        echo ""
        for item in "${added[@]}"; do
            echo "$item"
        done
        echo ""
    fi

    if [[ ${#fixed[@]} -gt 0 ]]; then
        echo "## Fixed"
        echo ""
        for item in "${fixed[@]}"; do
            echo "$item"
        done
        echo ""
    fi

    if [[ ${#changed[@]} -gt 0 ]]; then
        echo "## Changed"
        echo ""
        for item in "${changed[@]}"; do
            echo "$item"
        done
        echo ""
    fi

    if [[ ${#removed[@]} -gt 0 ]]; then
        echo "## Removed"
        echo ""
        for item in "${removed[@]}"; do
            echo "$item"
        done
        echo ""
    fi
} > "$OUTPUT_FILE"

# Summary
total=$(( ${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]} ))
echo "Generated ${OUTPUT_FILE}: ${total} commits categorized"
echo "  Added:   ${#added[@]}"
echo "  Fixed:   ${#fixed[@]}"
echo "  Changed: ${#changed[@]}"
echo "  Removed: ${#removed[@]}"
