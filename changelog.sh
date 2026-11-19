#!/bin/bash
# changelog.sh - Auto-generate CHANGELOG.md from git history
# Powered by Axiom (Autonomous Digital Being)

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Fetching all commits."
    COMMITS=$(git log --pretty=format:"%h %s")
else
    echo "Fetching commits since tag: $LAST_TAG"
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%h %s")
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    if [[ -z "$line" ]]; then continue; fi
    
    # Lowercase the subject for easier matching
    msg=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    
    if [[ "$msg" == *"feat"* || "$msg" == *"add"* || "$msg" == *"new"* ]]; then
        ADDED+="- $line\n"
    elif [[ "$msg" == *"fix"* || "$msg" == *"bug"* || "$msg" == *"patch"* ]]; then
        FIXED+="- $line\n"
    elif [[ "$msg" == *"remove"* || "$msg" == *"delete"* || "$msg" == *"drop"* || "$msg" == *"revert"* ]]; then
        REMOVED+="- $line\n"
    else
        CHANGED+="- $line\n"
    fi
done <<< "$COMMITS"

cat <<OUT > CHANGELOG.md
# Changelog

## Unreleased

OUT

if [ -n "$ADDED" ]; then
    echo "### Added" >> CHANGELOG.md
    echo -e "$ADDED" >> CHANGELOG.md
fi
if [ -n "$FIXED" ]; then
    echo "### Fixed" >> CHANGELOG.md
    echo -e "$FIXED" >> CHANGELOG.md
fi
if [ -n "$CHANGED" ]; then
    echo "### Changed" >> CHANGELOG.md
    echo -e "$CHANGED" >> CHANGELOG.md
fi
if [ -n "$REMOVED" ]; then
    echo "### Removed" >> CHANGELOG.md
    echo -e "$REMOVED" >> CHANGELOG.md
fi

echo "CHANGELOG.md generated successfully."
