#!/usr/bin/env bash
set -e

shopt -s nocasematch

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"%s" 2>/dev/null || true)
else
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s" 2>/dev/null || true)
fi

if [ -z "$COMMITS" ]; then
    echo "No new commits found."
    exit 0
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS= read -r msg; do
    [ -z "$msg" ] && continue
    if [[ "$msg" =~ ^(feat|add)[^:]*:\ (.*) ]]; then
        ADDED+=("- ${BASH_REMATCH[2]}")
    elif [[ "$msg" =~ ^(fix|bug)[^:]*:\ (.*) ]]; then
        FIXED+=("- ${BASH_REMATCH[2]}")
    elif [[ "$msg" =~ ^(remove|del|delete|drop)[^:]*:\ (.*) ]]; then
        REMOVED+=("- ${BASH_REMATCH[2]}")
    elif [[ "$msg" =~ ^(refactor|chore|update|change|docs|style|test)[^:]*:\ (.*) ]]; then
        CHANGED+=("- ${BASH_REMATCH[2]}")
    else
        CHANGED+=("- $msg")
    fi
done <<< "$COMMITS"

DATE=$(date +%Y-%m-%d)
OUT="## [$DATE]\n"

if [ ${#ADDED[@]} -gt 0 ]; then
    OUT+="\n### Added\n$(printf "%s\n" "${ADDED[@]}")\n"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    OUT+="\n### Fixed\n$(printf "%s\n" "${FIXED[@]}")\n"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    OUT+="\n### Changed\n$(printf "%s\n" "${CHANGED[@]}")\n"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    OUT+="\n### Removed\n$(printf "%s\n" "${REMOVED[@]}")\n"
fi

echo -e "$OUT" > CHANGELOG_tmp.md

if [ -f CHANGELOG.md ]; then
    # Prevent duplicate prepend if running multiple times on same day without new tags
    # This is a basic prepend
    cat CHANGELOG_tmp.md CHANGELOG.md > CHANGELOG_new.md
    mv CHANGELOG_new.md CHANGELOG.md
    rm CHANGELOG_tmp.md
else
    mv CHANGELOG_tmp.md CHANGELOG.md
fi

echo "CHANGELOG.md generated and updated successfully."
