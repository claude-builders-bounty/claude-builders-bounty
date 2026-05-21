#!/usr/bin/env bash
set -euo pipefail

CHANGELOG_FILE="CHANGELOG.md"
FROM_REF=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --from)
            FROM_REF="$2"
            shift 2
            ;;
        --output)
            CHANGELOG_FILE="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [ -z "$FROM_REF" ]; then
    FROM_REF=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -z "$FROM_REF" ]; then
    COMMITS=$(git log --pretty=format:"%s" --reverse)
else
    COMMITS=$(git log "${FROM_REF}..HEAD" --pretty=format:"%s" --reverse)
fi

if [ -z "$COMMITS" ]; then
    echo "No new commits found."
    exit 0
fi

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
if [ "$LAST_TAG" = "0.0.0" ]; then
    VERSION="0.1.0"
else
    MAJOR=$(echo "$LAST_TAG" | sed 's/^v//' | cut -d. -f1)
    MINOR=$(echo "$LAST_TAG" | sed 's/^v//' | cut -d. -f2)
    PATCH=$(echo "$LAST_TAG" | sed 's/^v//' | cut -d. -f3 | cut -d- -f1)
    VERSION="${MAJOR}.$((MINOR + 1)).0"
fi

TODAY=$(date -u +"%Y-%m-%d")

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r msg; do
    lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    if echo "$lower" | grep -qiE "^(feat|add|new|feature)[:\!]"; then
        ADDED="${ADDED}- ${msg}\n"
    elif echo "$lower" | grep -qiE "^(fix|bug|patch|hotfix)[:\!]"; then
        FIXED="${FIXED}- ${msg}\n"
    elif echo "$lower" | grep -qiE "^(remove|delete|deprecate)[:\!]"; then
        REMOVED="${REMOVED}- ${msg}\n"
    elif echo "$lower" | grep -qiE "^(refactor|update|change|improve|perf|chore)[:\!]"; then
        CHANGED="${CHANGED}- ${msg}\n"
    else
        CHANGED="${CHANGED}- ${msg}\n"
    fi
done <<< "$COMMITS"

ENTRY="# Changelog\n\n## [${VERSION}] - ${TODAY}\n"

if [ -n "$ADDED" ]; then
    ENTRY="${ENTRY}\n### Added\n${ADDED}"
fi
if [ -n "$FIXED" ]; then
    ENTRY="${ENTRY}\n### Fixed\n${FIXED}"
fi
if [ -n "$CHANGED" ]; then
    ENTRY="${ENTRY}\n### Changed\n${CHANGED}"
fi
if [ -n "$REMOVED" ]; then
    ENTRY="${ENTRY}\n### Removed\n${REMOVED}"
fi

TEMP_FILE=$(mktemp)
echo -e "$ENTRY" > "$TEMP_FILE"

if [ -f "$CHANGELOG_FILE" ]; then
    {
        echo -e "$ENTRY"
        echo ""
        tail -n +2 "$CHANGELOG_FILE"
    } > "${CHANGELOG_FILE}.tmp"
    mv "${CHANGELOG_FILE}.tmp" "$CHANGELOG_FILE"
else
    echo -e "$ENTRY" > "$CHANGELOG_FILE"
fi

echo "CHANGELOG.md generated with version ${VERSION} (${TODAY})"

if [ -n "$FROM_REF" ]; then
    echo "Commits since ${FROM_REF}:"
else
    echo "Commits since beginning of history"
fi