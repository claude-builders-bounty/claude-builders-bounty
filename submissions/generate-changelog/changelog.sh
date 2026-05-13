#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag|commit>] [--output <file>]

OUTPUT="CHANGELOG.md"
SINCE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--since <tag|commit>] [--output <file>]"
      echo "  --since   Start from this tag/commit (default: last tag)"
      echo "  --output  Output file (default: CHANGELOG.md)"
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: not a git repository"
  exit 1
fi

# Find the range to generate changelog for
if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..HEAD"
  echo "Generating changelog since tag: $SINCE"
else
  RANGE=""
  echo "Generating changelog for all commits (no previous tag found)"
fi

# Get current version from latest tag or use Unreleased
CURRENT_VERSION=$(git describe --tags --abbrev=0 HEAD 2>/dev/null || echo "Unreleased")
CURRENT_DATE=$(date +%Y-%m-%d)

# Collect commits and categorize them
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS= read -r line; do
  [[ -z "$line" ]] && continue

  msg_lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')

  if echo "$msg_lower" | grep -qE '^(feat|add|new|create|implement|introduce)(\(|:| )'; then
    ADDED="${ADDED}\n- ${line}"
  elif echo "$msg_lower" | grep -qE '^(fix|bug|patch|resolve|close|repair)(\(|:| )'; then
    FIXED="${FIXED}\n- ${line}"
  elif echo "$msg_lower" | grep -qE '^(remove|delete|drop|deprecate|uninstall)(\(|:| )'; then
    REMOVED="${REMOVED}\n- ${line}"
  elif echo "$msg_lower" | grep -qE '^(refactor|update|change|modify|improve|enhance|perf|style|chore|ci|build|docs|test)(\(|:| )'; then
    CHANGED="${CHANGED}\n- ${line}"
  else
    # Try keyword-based categorization for non-conventional commits
    if echo "$msg_lower" | grep -qE '\b(add|added|new|create|implement|introduce)\b'; then
      ADDED="${ADDED}\n- ${line}"
    elif echo "$msg_lower" | grep -qE '\b(fix|fixed|bug|patch|resolve|repair)\b'; then
      FIXED="${FIXED}\n- ${line}"
    elif echo "$msg_lower" | grep -qE '\b(remove|removed|delete|deleted|drop|deprecate)\b'; then
      REMOVED="${REMOVED}\n- ${line}"
    else
      CHANGED="${CHANGED}\n- ${line}"
    fi
  fi
done < <(git log ${RANGE} --pretty=format:"%s" --no-merges 2>/dev/null)

# Build the changelog
{
  echo "# Changelog"
  echo ""
  echo "## [${CURRENT_VERSION}] - ${CURRENT_DATE}"
  echo ""

  if [[ -n "$ADDED" ]]; then
    echo "### Added"
    echo -e "$ADDED"
    echo ""
  fi

  if [[ -n "$FIXED" ]]; then
    echo "### Fixed"
    echo -e "$FIXED"
    echo ""
  fi

  if [[ -n "$CHANGED" ]]; then
    echo "### Changed"
    echo -e "$CHANGED"
    echo ""
  fi

  if [[ -n "$REMOVED" ]]; then
    echo "### Removed"
    echo -e "$REMOVED"
    echo ""
  fi
} > "$OUTPUT"

TOTAL=$(git log ${RANGE} --pretty=format:"%s" --no-merges 2>/dev/null | wc -l | tr -d ' ')
echo "Generated ${OUTPUT} with ${TOTAL} commits categorized."
