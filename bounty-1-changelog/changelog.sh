#!/usr/bin/env bash
# CHANGELOG Generator — ./changelog.sh [--repo PATH] [--output CHANGELOG.md]
# Fetches git commits since last tag, auto-categorizes into Added/Fixed/Changed/Removed

set -euo pipefail

REPO="${PWD}"
OUTPUT="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo) REPO="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        *) echo "Usage: $0 [--repo PATH] [--output FILE]"; exit 1 ;;
    esac
done

cd "$REPO"

# Find last tag or use initial commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
    RANGE="HEAD"
    VERSION="0.1.0"
else
    RANGE="${LAST_TAG}..HEAD"
    VERSION="${LAST_TAG}"
fi

# Get current date
DATE=$(date +%Y-%m-%d)

# Fetch commits and categorize
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS= read -r line; do
    msg=$(echo "$line" | sed -E 's/^[a-f0-9]+ //')
    lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

    if echo "$lower_msg" | grep -qE '^(feat|add|new|feature| implement)'; then
        ADDED+=("$msg")
    elif echo "$lower_msg" | grep -qE '^(fix|bug|hotfix|patch|correct)'; then
        FIXED+=("$msg")
    elif echo "$lower_msg" | grep -qE '^(remove|drop|delete|deprecat|clean)'; then
        REMOVED+=("$msg")
    else
        CHANGED+=("$msg")
    fi
done < <(git log --oneline "$RANGE" 2>/dev/null)

# Generate CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "## [${VERSION}] - ${DATE}"
    echo ""

    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        for c in "${ADDED[@]}"; do echo "- ${c}"; done
        echo ""
    fi

    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        for c in "${FIXED[@]}"; do echo "- ${c}"; done
        echo ""
    fi

    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        for c in "${CHANGED[@]}"; do echo "- ${c}"; done
        echo ""
    fi

    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        for c in "${REMOVED[@]}"; do echo "- ${c}"; done
        echo ""
    fi

    if [ $(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} )) -eq 0 ]; then
        echo "_No changes since last tag._"
        echo ""
    fi
} > "$OUTPUT"

echo "CHANGELOG generated: $(pwd)/${OUTPUT}"
echo "  Added: ${#ADDED[@]}, Fixed: ${#FIXED[@]}, Changed: ${#CHANGED[@]}, Removed: ${#REMOVED[@]}"
