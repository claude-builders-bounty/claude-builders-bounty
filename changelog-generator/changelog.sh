#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [since_tag] [--repo /path/to/repo]
# If no tag is provided, uses the most recent git tag as the starting point.

set -eo pipefail
shopt -s nullglob

REPO_DIR="."
SINCE_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO_DIR="$2"
      shift 2
      ;;
    *)
      SINCE_TAG="$1"
      shift
      ;;
  esac
done

cd "$REPO_DIR"

# Determine the starting tag
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -z "$SINCE_TAG" ]]; then
    # No tags exist; use the first commit
    SINCE_TAG=$(git rev-list --max-parents=0 HEAD 2>/dev/null | head -1)
    if [[ -z "$SINCE_TAG" ]]; then
      echo "Error: No git history found." >&2
      exit 1
    fi
    RANGE="$SINCE_TAG..HEAD"
  else
    RANGE="$SINCE_TAG..HEAD"
  fi
else
  RANGE="$SINCE_TAG..HEAD"
fi

# Fetch commits since the tag
COMMITS=$(git log "$RANGE" --pretty=format:"%H|%s|%an|%ad" --date=short 2>/dev/null)

if [[ -z "$COMMITS" ]]; then
  echo "No commits found since $SINCE_TAG."
  exit 0
fi

# Initialize categories
declare -a ADDED FIXED CHANGED REMOVED

while IFS='|' read -r hash subject author date; do
  # Normalize the subject to lowercase for categorization
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^(add|feat|create|implement|introduce|support|new)'; then
    ADDED+=("- $subject ($author, $date)")
  elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|repair|correct|hotfix)'; then
    FIXED+=("- $subject ($author, $date)")
  elif echo "$lower" | grep -qE '^(change|update|modify|refactor|improve|enhance|bump|upgrade|migrate|rename|move)'; then
    CHANGED+=("- $subject ($author, $date)")
  elif echo "$lower" | grep -qE '^(remove|delete|drop|strip|deprecate)'; then
    REMOVED+=("- $subject ($author, $date)")
  else
    # Default to Changed if no pattern matches
    CHANGED+=("- $subject ($author, $date)")
  fi
done <<< "$COMMITS"

# Determine version label
if git rev-parse "$SINCE_TAG" >/dev/null 2>&1 && git tag -l "$SINCE_TAG" | grep -q .; then
  VERSION="$(date +%Y-%m-%d)"
  PREV_VERSION="$SINCE_TAG"
else
  VERSION="Initial"
  PREV_VERSION="(first commit)"
fi

# Generate CHANGELOG.md
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project are documented here."
  echo "Generated automatically by \`changelog.sh\`."
  echo ""
  echo "## [$VERSION] - $(date +%Y-%m-%d)"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    printf '%s\n' "${ADDED[@]}"
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    printf '%s\n' "${FIXED[@]}"
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    printf '%s\n' "${CHANGED[@]}"
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    printf '%s\n' "${REMOVED[@]}"
    echo ""
  fi

  echo "---"
  echo "_Base: $PREV_VERSION → Head: HEAD_"
} > CHANGELOG.md

echo "✅ CHANGELOG.md generated with ${#ADDED[@]} added, ${#FIXED[@]} fixed, ${#CHANGED[@]} changed, ${#REMOVED[@]} removed entries."
