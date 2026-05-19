#!/bin/bash

# Auto-generate a structured CHANGELOG.md from git history

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"%s")
    OUTPUT_TITLE="## Initial Release"
else
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"%s")
    OUTPUT_TITLE="## Changes since $LAST_TAG"
fi

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while read -r msg; do
    # check prefix
    LOWER_MSG=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
    
    if [[ $LOWER_MSG == feat* ]] || [[ $LOWER_MSG == add* ]]; then
        ADDED="$ADDED\n- $msg"
    elif [[ $LOWER_MSG == fix* ]] || [[ $LOWER_MSG == bug* ]]; then
        FIXED="$FIXED\n- $msg"
    elif [[ $LOWER_MSG == refactor* ]] || [[ $LOWER_MSG == update* ]] || [[ $LOWER_MSG == chore* ]]; then
        CHANGED="$CHANGED\n- $msg"
    elif [[ $LOWER_MSG == remove* ]] || [[ $LOWER_MSG == delete* ]] || [[ $LOWER_MSG == drop* ]]; then
        REMOVED="$REMOVED\n- $msg"
    else
        if [ ! -z "$msg" ]; then
            OTHER="$OTHER\n- $msg"
        fi
    fi
done <<< "$COMMITS"

cat <<EOT > CHANGELOG.md
# CHANGELOG

$OUTPUT_TITLE
EOT

if [ ! -z "$ADDED" ]; then
    echo -e "\n### Added$ADDED" >> CHANGELOG.md
fi
if [ ! -z "$FIXED" ]; then
    echo -e "\n### Fixed$FIXED" >> CHANGELOG.md
fi
if [ ! -z "$CHANGED" ]; then
    echo -e "\n### Changed$CHANGED" >> CHANGELOG.md
fi
if [ ! -z "$REMOVED" ]; then
    echo -e "\n### Removed$REMOVED" >> CHANGELOG.md
fi
if [ ! -z "$OTHER" ]; then
    echo -e "\n### Other$OTHER" >> CHANGELOG.md
fi

echo "CHANGELOG.md has been generated successfully."
