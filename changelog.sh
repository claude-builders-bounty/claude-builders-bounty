#!/usr/bin/env bash

set -euo pipefail

# Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--to <commit>] [--output CHANGELOG.md]

# Default values
OUTPUT_FILE="CHANGELOG.md"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --since)
      SINCE_TAG="$2"
      shift 2
      ;;
    --to)
      TO_COMMIT="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

# Check if we are in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository" >&2
  exit 1
fi

# Determine the git log range
if [ -z "${SINCE_TAG:-}" ]; then
  # Get the latest tag (or start from beginning)
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -z "${TO_COMMIT:-}" ]; then
  TO_COMMIT="HEAD"
fi

if [ -n "$SINCE_TAG" ]; then
  RANGE="${SINCE_TAG}..${TO_COMMIT}"
  VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
  DATE=$(date +%Y-%m-%d)
else
  RANGE="${TO_COMMIT}"
  VERSION="v0.1.0"
  DATE=$(date +%Y-%m-%d)
fi

# Get commit log
COMMITS=$(git log --oneline --no-decorate --format="%H %s" "$RANGE" 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
  echo "No new commits since last tag."
  exit 0
fi

# Categorize commits
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

IFS=$'\n'
for COMMIT in $COMMITS; do
  HASH=$(echo "$COMMIT" | cut -d' ' -f1)
  MESSAGE=$(echo "$COMMIT" | cut -d' ' -f2-)
  # Remove leading type (e.g., feat:, fix:, etc.)
  if [[ "$MESSAGE" =~ ^(feat|feature)(\(.*\))?!?:\ (.*) ]]; then
    ADDED+=("${BASH_REMATCH[3]}")
  elif [[ "$MESSAGE" =~ ^fix(\(.*\))?!?:\ (.*) ]]; then
    FIXED+=("${BASH_REMATCH[2]}")
  elif [[ "$MESSAGE" =~ ^refactor(\(.*\))?!?:\ (.*) ]]; then
    CHANGED+=("${BASH_REMATCH[2]}")
  elif [[ "$MESSAGE" =~ ^perf(\(.*\))?!?:\ (.*) ]]; then
    CHANGED+=("${BASH_REMATCH[2]}")
  elif [[ "$MESSAGE" =~ ^removed(\(.*\))?!?:\ (.*) ]]; then
    REMOVED+=("${BASH_REMATCH[2]}")
  else
    OTHER+=("$MESSAGE")
  fi
done

# Generate CHANGELOG.md
{
  echo "# Changelog"
  echo ""
  echo "## [$VERSION] - $DATE"
  echo ""

  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added"
    for msg in "${ADDED[@]}"; do
      echo "- $msg"
    done
    echo ""
  fi

  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed"
    for msg in "${FIXED[@]}"; do
      echo "- $msg"
    done
    echo ""
  fi

  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed"
    for msg in "${CHANGED[@]}"; do
      echo "- $msg"
    done
    echo ""
  fi

  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed"
    for msg in "${REMOVED[@]}"; do
      echo "- $msg"
    done
    echo ""
  fi

  if [ ${#OTHER[@]} -gt 0 ]; then
    echo "### Other"
    for msg in "${OTHER[@]}"; do
      echo "- $msg"
    done
    echo ""
  fi
} > "$OUTPUT_FILE"

echo "Changelog generated at $OUTPUT_FILE"
