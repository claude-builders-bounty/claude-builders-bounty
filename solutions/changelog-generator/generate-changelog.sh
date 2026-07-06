#!/usr/bin/env bash
# generate-changelog — Generate a structured CHANGELOG.md from git history
# Usage: ./generate-changelog.sh [--output CHANGELOG.md]

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_DIR="${2:-.}"

cd "$REPO_DIR"

# Get last tag or first commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)
SINCE_RANGE="${LAST_TAG}..HEAD"

echo "Generating changelog from ${LAST_TAG} to HEAD..."
echo "Output: ${OUTPUT_FILE}"

# Categorize commits
ADDED=$(git log "$SINCE_RANGE" --grep="^feat\|^add\|^feature" --oneline 2>/dev/null || echo "")
FIXED=$(git log "$SINCE_RANGE" --grep="^fix\|^bug\|^hotfix\|^patch" --oneline 2>/dev/null || echo "")
CHANGED=$(git log "$SINCE_RANGE" --grep="^refactor\|^perf\|^update\|^change\|^upgrade" --oneline 2>/dev/null || echo "")
REMOVED=$(git log "$SINCE_RANGE" --grep="^remove\|^deprecate\|^delete\|^drop" --oneline 2>/dev/null || echo "")
DOCS=$(git log "$SINCE_RANGE" --grep="^docs\|^doc\|^readme" --oneline 2>/dev/null || echo "")
DEPS=$(git log "$SINCE_RANGE" --grep="^deps\|^depend\|^bump" --oneline 2>/dev/null || echo "")

# Count
COUNT_ADDED=$(echo "$ADDED" | grep -c . || true)
COUNT_FIXED=$(echo "$FIXED" | grep -c . || true)
COUNT_CHANGED=$(echo "$CHANGED" | grep -c . || true)
COUNT_REMOVED=$(echo "$REMOVED" | grep -c . || true)
COUNT_DOCS=$(echo "$DOCS" | grep -c . || true)
COUNT_DEPS=$(echo "$DEPS" | grep -c . || true)

# Build changelog
{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased] - $(date +%Y-%m-%d)"
  echo ""

  if [[ $COUNT_ADDED -gt 0 ]]; then
    echo "### Added"
    echo "$ADDED" | while IFS= read -r line; do
      echo "- ${line}"
    done
    echo ""
  fi

  if [[ $COUNT_FIXED -gt 0 ]]; then
    echo "### Fixed"
    echo "$FIXED" | while IFS= read -r line; do
      echo "- ${line}"
    done
    echo ""
  fi

  if [[ $COUNT_CHANGED -gt 0 ]]; then
    echo "### Changed"
    echo "$CHANGED" | while IFS= read -r line; do
      echo "- ${line}"
    done
    echo ""
  fi

  if [[ $COUNT_REMOVED -gt 0 ]]; then
    echo "### Removed"
    echo "$REMOVED" | while IFS= read -r line; do
      echo "- ${line}"
    done
    echo ""
  fi

  if [[ $COUNT_DOCS -gt 0 ]]; then
    echo "### Documentation"
    echo "$DOCS" | while IFS= read -r line; do
      echo "- ${line}"
    done
    echo ""
  fi

  if [[ $COUNT_DEPS -gt 0 ]]; then
    echo "### Dependencies"
    echo "$DEPS" | while IFS= read -r line; do
      echo "- ${line}"
    done
    echo ""
  fi

  echo "---"
  echo "**Total commits since ${LAST_TAG}: $((COUNT_ADDED + COUNT_FIXED + COUNT_CHANGED + COUNT_REMOVED + COUNT_DOCS + COUNT_DEPS))**"
} > "${OUTPUT_FILE}"

echo "Done! Changelog written to ${OUTPUT_FILE}"
echo "  Added: ${COUNT_ADDED}"
echo "  Fixed: ${COUNT_FIXED}"
echo "  Changed: ${COUNT_CHANGED}"
echo "  Removed: ${COUNT_REMOVED}"
echo "  Docs: ${COUNT_DOCS}"
echo "  Dependencies: ${COUNT_DEPS}"
