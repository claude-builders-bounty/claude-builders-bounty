#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# changelog.sh — Generate structured CHANGELOG.md from git log
# Usage: ./changelog.sh [--repo <path>] [--output <file>]
# ============================================================

REPO="."
OUTPUT="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)    REPO="$2"; shift 2 ;;
        --output)  OUTPUT="$2"; shift 2 ;;
        *)         echo "Unknown option: $1"; exit 1 ;;
    esac
done

cd "$REPO"

# Find the last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -z "$LAST_TAG" ]]; then
    echo "No tags found. Generating changelog from all commits."
    RANGE="HEAD"
    TAG_LINE="(initial release)"
else
    RANGE="${LAST_TAG}..HEAD"
    TAG_LINE="since ${LAST_TAG}"
fi

# Get current date
DATE=$(date +%Y-%m-%d)

# Initialize sections
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

# Parse each commit
while IFS='|' read -r HASH MSG; do
    # Remove trailing newline
    MSG="${MSG%$'\n'}"
    # Check conventional commit prefix
    if [[ "$MSG" =~ ^(feat|feature)($|[\(:]) ]]; then
        ADDED+=("$MSG")
    elif [[ "$MSG" =~ ^fix($|[\(:]) ]]; then
        FIXED+=("$MSG")
    elif [[ "$MSG" =~ ^(BREAKING[[:space:]]*CHANGE|major)($|[\(:]) ]]; then
        CHANGED+=("⚠️ $MSG")
    elif [[ "$MSG" =~ ^(refactor|perf|improve)($|[\(:]) ]]; then
        CHANGED+=("$MSG")
    elif [[ "$MSG" =~ ^remove($|[\(:]) ]]; then
        REMOVED+=("$MSG")
    elif [[ "$MSG" =~ ^(chore|docs|test|style|build|ci)($|[\(:]) ]]; then
        OTHER+=("$MSG")
    else
        # Keyword-based fallback
        LOWMSG="${MSG,,}"
        if [[ "$LOWMSG" =~ ^(add|new|create|implement|support) ]]; then
            ADDED+=("$MSG")
        elif [[ "$LOWMSG" =~ ^(fix|correct|resolve|patch|hotfix) ]]; then
            FIXED+=("$MSG")
        elif [[ "$LOWMSG" =~ ^(change|update|upgrade|migrate|refactor|improve) ]]; then
            CHANGED+=("$MSG")
        elif [[ "$LOWMSG" =~ ^(remove|deprecate|delete|drop) ]]; then
            REMOVED+=("$MSG")
        else
            OTHER+=("$MSG")
        fi
    fi
done < <(git log --oneline --format="%h|%s" "$RANGE" 2>/dev/null || echo "")

# Generate the CHANGELOG markdown
{
    echo "# Changelog"
    echo ""
    echo "## [Unreleased] - ${DATE}"
    echo ""
    echo "*Generated from commits ${TAG_LINE}*"
    echo ""

    write_section() {
        local title="$1" emoji="$2"
        shift 2
        local items=("$@")
        if [[ ${#items[@]} -gt 0 ]]; then
            echo "### ${emoji} ${title}"
            for item in "${items[@]}"; do
                echo "- ${item}"
            done
            echo ""
        fi
    }

    write_section "Added" "🎉" "${ADDED[@]}"
    write_section "Fixed" "🐛" "${FIXED[@]}"
    write_section "Changed" "🔄" "${CHANGED[@]}"
    write_section "Removed" "🗑️" "${REMOVED[@]}"

    if [[ ${#OTHER[@]} -gt 0 ]]; then
        echo "### 🔧 Maintenance"
        for item in "${OTHER[@]}"; do
            echo "- ${item}"
        done
        echo ""
    fi

} > "$OUTPUT"

echo "✅ Generated $OUTPUT with $((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]})) entries"
