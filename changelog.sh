#!/bin/bash
# Generate CHANGELOG.md from git history since last tag

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

echo "# Changelog" > CHANGELOG.md
echo "" >> CHANGELOG.md
echo "## [Unreleased] - $(date +%Y-%m-%d)" >> CHANGELOG.md
echo "" >> CHANGELOG.md

git log "$LAST_TAG..HEAD" --pretty=format:"%s" | while read -r line; do
  case "$line" in
    feat:*|feature:*|Added*) echo "### Added" >> CHANGELOG.md ;;
    fix:*|Fixed*) echo "### Fixed" >> CHANGELOG.md ;;
    changed:*|Changed*|refactor:*) echo "### Changed" >> CHANGELOG.md ;;
    removed:*|Removed*|delete:*) echo "### Removed" >> CHANGELOG.md ;;
    chore:*|docs:*|test:*|ci:*) echo "### Maintenance" >> CHANGELOG.md ;;
  esac
done

echo "CHANGELOG.md generated successfully."
