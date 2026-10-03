#!/usr/bin/env bash
set -euo pipefail

# CHANGELOG Generator from git history
# Usage: ./changelog.sh [OUTPUT_FILE]
#   Default output: CHANGELOG.md in current directory

OUTPUT="${1:-CHANGELOG.md}"

# Find the most recent tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [[ -z "$LATEST_TAG" ]]; then
  # No tags exist; use all history
  COMMITS=$(git log --pretty=format:"%s" --reverse)
else
  COMMITS=$(git log "${LATEST_TAG}..HEAD" --pretty=format:"%s" --reverse)
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found since tag '$LATEST_TAG'."
  exit 0
fi

# Conventional commit prefixes and their categories
declare -A PREFIX_CATEGORY
PREFIX_CATEGORY["feat"]="Added"
PREFIX_CATEGORY["fix"]="Fixed"
PREFIX_CATEGORY["refactor"]="Changed"
PREFIX_CATEGORY["docs"]="Changed"
PREFIX_CATEGORY["chore"]="Changed"
PREFIX_CATEGORY["style"]="Changed"
PREFIX_CATEGORY["perf"]="Changed"
PREFIX_CATEGORY["build"]="Changed"
PREFIX_CATEGORY["ci"]="Changed"
PREFIX_CATEGORY["test"]="Changed"
PREFIX_CATEGORY["revert"]="Removed"

# Arrays for each category
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
UNCATEGORIZED=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  # Extract prefix (e.g., "feat", "fix") from the beginning of the commit message
  PREFIX=$(echo "$line" | grep -oE '^[a-z]+(?=:)' || true)
  CATEGORY="${PREFIX_CATEGORY[$PREFIX]:-}"

  if [[ -n "$CATEGORY" ]]; then
    case "$CATEGORY" in
      "Added") ADDED+=("$line") ;;
      "Fixed") FIXED+=("$line") ;;
      "Changed") CHANGED+=("$line") ;;
      "Removed") REMOVED+=("$line") ;;
    esac
  else
    UNCATEGORIZED+=("$line")
  fi
done <<< "$COMMITS"

# Build CHANGELOG content
{
  TAG_DATE=$(git log -1 --format=%ai "$LATEST_TAG" 2>/dev/null || date +%Y-%m-%d)
  VERSION="${LATEST_TAG:-Unreleased}"
  echo "# Changelog"
  echo ""
  echo "## $VERSION — $(echo "$TAG_DATE" | cut -d' ' -f1)"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    echo ""
    for item in "${ADDED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    echo ""
    for item in "${FIXED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    echo ""
    for item in "${CHANGED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    echo ""
    for item in "${REMOVED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi

  if [[ ${#UNCATEGORIZED[@]} -gt 0 ]]; then
    echo "### Other"
    echo ""
    for item in "${UNCATEGORIZED[@]}"; do
      echo "- $item"
    done
    echo ""
  fi
} > "$OUTPUT"

echo "Generated $OUTPUT from $LATEST_TAG (or beginning of history if no tags exist)."
