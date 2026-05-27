#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

{
  echo "# Changelog"
  echo ""
  echo "All notable changes will be documented in this file."
  echo ""

  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

  if [ -n "$LATEST_TAG" ]; then
    echo "## [$LATEST_TAG]"
  else
    echo "## [Unreleased]"
  fi
  echo ""

  echo "### Added"
  git log --oneline --grep="^feat" 2>/dev/null | sed 's/^/  - /' || echo "  (none)"
  echo ""

  echo "### Fixed"
  git log --oneline --grep="^fix" 2>/dev/null | sed 's/^/  - /' || echo "  (none)"
  echo ""

  echo "### Changed"
  git log --oneline --grep="^refactor\|^update\|^perf" 2>/dev/null | sed 's/^/  - /' || echo "  (none)"
  echo ""

  echo "### Removed"
  git log --oneline --grep="^remove\|^deprecate" 2>/dev/null | sed 's/^/  - /' || echo "  (none)"

} > "$OUTPUT"

echo "Generated $OUTPUT"
