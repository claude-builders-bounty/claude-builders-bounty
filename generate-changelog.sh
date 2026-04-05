#!/bin/bash
set -eo pipefail

# 1. Dependency check
if ! command -v claude &> /dev/null; then
    echo "Error: 'claude' CLI is not installed or not in PATH."
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "Error: 'git' is not installed."
    exit 1
fi

# 2. Get commits safely
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
    echo "No previous tags found. Fetching all commits (up to 500)..."
    COMMITS=$(git log --pretty=format:"- %s" -n 500)
else
    echo "Fetching commits since tag: $LAST_TAG..."
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"- %s" -n 500)
fi

if [ -z "$COMMITS" ]; then
    echo "No new commits found since last tag. Exiting."
    exit 0
fi

# 3. Create a secure temp file
PROMPT_FILE=$(mktemp)

# Clean up trap
trap 'rm -f "$PROMPT_FILE"' EXIT

# 4. Write prompt literally (no interpolation)
cat << 'PROMPT_EOF' > "$PROMPT_FILE"
You are a strict release notes generator. Group the following commit messages exactly into these categories:
### Added
### Fixed
### Changed
### Removed

Do not include empty categories. Format as valid Markdown.

Commits:
PROMPT_EOF

# Append commits safely without expanding any $VARIABLES inside commit messages
echo "$COMMITS" >> "$PROMPT_FILE"

echo "Sending commits to Claude..."
cat "$PROMPT_FILE" | claude -p "Generate CHANGELOG.md" > CHANGELOG_NEW.md

echo "Successfully generated CHANGELOG_NEW.md"
