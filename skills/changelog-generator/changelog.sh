#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history.
# Usage: ./changelog.sh [--output FILE]
# Categories: Added / Fixed / Changed / Removed (follows keepachangelog.com)
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"
cd "$REPO_ROOT"

OUTPUT="${2:-CHANGELOG.md}"
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo '')"

if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
    VERSION="${LAST_TAG}"
else
    RANGE="$(git rev-list --max-parents=0 HEAD)..HEAD"
    VERSION="Unreleased"
fi

TODAY="$(date +%Y-%m-%d)"

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r msg; do
    [ -z "$msg" ] && continue
    msg="$(echo "$msg" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

    # Detect conventional commit type and scope
    if echo "$msg" | grep -qiE '^(feat|add|implement|introduce|create)'; then
        ADDED+="- $(echo "$msg" | sed 's/^[^:]*: //')"$'\n'
    elif echo "$msg" | grep -qiE '^(fix|bug|resolve|patch|correct|hotfix)'; then
        FIXED+="- $(echo "$msg" | sed 's/^[^:]*: //')"$'\n'
    elif echo "$msg" | grep -qiE '^(remove|drop|delete|deprecate|revert)'; then
        REMOVED+="- $(echo "$msg" | sed 's/^[^:]*: //')"$'\n'
    elif echo "$msg" | grep -qiE '^(chore|refactor|style|docs|test|ci|perf|build)'; then
        CHANGED+="- $(echo "$msg" | sed 's/^[^:]*: //')"$'\n'
    else
        CHANGED+="- ${msg}"$'\n'
    fi
done < <(git log "$RANGE" --pretty=format:"%s" 2>/dev/null)

{
    echo "# Changelog"
    echo ""
    echo "## ${VERSION} (${TODAY})"
    echo ""

    for cat in "Added" "Fixed" "Changed" "Removed"; do
        content=""
        case $cat in
            Added) content="$ADDED" ;;
            Fixed) content="$FIXED" ;;
            Changed) content="$CHANGED" ;;
            Removed) content="$REMOVED" ;;
        esac
        if [ -n "$content" ]; then
            echo "### $cat"
            echo ""
            printf '%s' "$content"
            echo ""
        fi
    done
} > "$OUTPUT"

echo "✓ CHANGELOG.md generated ($VERSION, $(echo "$RANGE" | xargs git log --oneline 2>/dev/null | wc -l) commits)"
