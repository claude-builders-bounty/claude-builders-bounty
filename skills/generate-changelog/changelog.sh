#!/bin/bash
# Generate CHANGELOG from git history
echo "# Changelog"
echo "## Unreleased"
echo "### Added"
git log --pretty=format:"- %s" -n 20 2>/dev/null | head -5
echo "### Fixed"
git log --pretty=format:"- %s" --grep="fix" -n 10 2>/dev/null | head -3
echo "### Changed"
git log --pretty=format:"- %s" --grep="chore" -n 10 2>/dev/null | head -3