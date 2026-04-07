#!/bin/bash

# changelog.sh - Script to generate a structured CHANGELOG.md from git history

# Check if CHANGELOG.md exists
if [ -f CHANGELOG.md ]; then
    echo "CHANGELOG.md already exists."
else
    touch CHANGELOG.md
fi

# Initialize sections in CHANGELOG.md

echo "# Changelog" > CHANGELOG.md

echo "All notable changes to this project will be documented in this file." >> CHANGELOG.md

echo -e "\n## [Unreleased]" >> CHANGELOG.md

# Fetch commits since the last tag and categorize them

git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:'%h - %s (%an)' | while IFS= read -r commit
do
    if [[ $commit == *"feat:"* ]]; then
        echo "- Added: ${commit#* - }" >> CHANGELOG.md
    elif [[ $commit == *"fix:"* ]]; then
        echo "- Fixed: ${commit#* - }" >> CHANGELOG.md
    elif [[ $commit == *"chore:"* ]]; then
        echo "- Changed: ${commit#* - }" >> CHANGELOG.md
    elif [[ $commit == *"BREAKING CHANGE:"* ]]; then
        echo "- Removed: ${commit#* - }" >> CHANGELOG.md
    fi
done

# Finalize the changelog entry

echo -e "\n## [Unreleased] - $(date +'%Y-%m-%d')" >> CHANGELOG.md

echo "Changelog generated successfully."