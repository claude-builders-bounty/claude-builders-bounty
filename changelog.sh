#!/usr/bin/env bash
#
# changelog.sh - Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh                    # Generate CHANGELOG.md
#   bash changelog.sh --output FILE.md   # Write to custom file
#   bash changelog.sh --since-tag v1.0   # Generate since a specific tag
#
# Requires: git

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --since-tag)
      SINCE_TAG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Get the git log range
if [[ -n "$SINCE_TAG" ]]; then
  COMMIT_RANGE="${SINCE_TAG}..HEAD"
else
  # Find the latest tag, or use all commits
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$LATEST_TAG" ]]; then
    COMMIT_RANGE="${LATEST_TAG}..HEAD"
  else
    COMMIT_RANGE="HEAD"
  fi
fi

echo "Generating changelog (range: ${COMMIT_RANGE})..."

# Categories
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

# Read commits and categorize
while IFS= read -r line; do
  [[ -z "$line" ]] && continue

  COMMIT_MSG=$(echo "$line" | sed 's/^[a-f0-9]* //')
  LOWER_MSG=$(echo "$COMMIT_MSG" | tr '[:upper:]' '[:lower:]')

  # Categorize based on conventional commit keywords
  if echo "$LOWER_MSG" | grep -qiE '\b(add|feat|implement|introduce|create|new)\b'; then
    ADDED+=("$COMMIT_MSG")
  elif echo "$LOWER_MSG" | grep -qiE '\b(fix|bug|repair|resolve|patch|correct)\b'; then
    FIXED+=("$COMMIT_MSG")
  elif echo "$LOWER_MSG" | grep -qiE '\b(update|change|modify|refactor|improve|enhance|upgrade|bump)\b'; then
    CHANGED+=("$COMMIT_MSG")
  elif echo "$LOWER_MSG" | grep -qiE '\b(remove|delete|drop|deprecate|clean|revert)\b'; then
    REMOVED+=("$COMMIT_MSG")
  else
    OTHER+=("$COMMIT_MSG")
  fi
done < <(git log "$COMMIT_RANGE" --pretty=format:"%h %s" --no-merges)

# Generate the CHANGELOG
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
  echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
  echo ""
  echo "## [Unreleased] - $(date +%Y-%m-%d)"
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

  if [[ ${#OTHER[@]} -gt 0 ]]; then
    echo "### Other"
    echo ""
    for item in "${OTHER[@]}"; do
      echo "- $item"
    done
    echo ""
  fi
} > "$OUTPUT_FILE"

echo "Changelog written to ${OUTPUT_FILE}"
echo "  Added:   ${#ADDED[@]}"
echo "  Fixed:   ${#FIXED[@]}"
echo "  Changed: ${#CHANGED[@]}"
echo "  Removed: ${#REMOVED[@]}"
echo "  Other:   ${#OTHER[@]}"
