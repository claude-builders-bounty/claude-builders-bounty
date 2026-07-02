#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>]
# Bounty: claude-builders-bounty#1

set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE_TAG=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)   SINCE_TAG="$2"; shift 2 ;;
    --output)  OUTPUT="$2";    shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--since <tag>] [--output <file>]"
      echo "  --since <tag>   Start from this tag (default: latest tag)"
      echo "  --output <file> Output file (default: CHANGELOG.md)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Determine the range
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -z "$SINCE_TAG" ]]; then
  RANGE="HEAD"
  RANGE_LABEL="(all commits)"
else
  RANGE="${SINCE_TAG}..HEAD"
  RANGE_LABEL="since ${SINCE_TAG}"
fi

TODAY=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")
NEXT_VERSION="Unreleased"

echo "🔍 Collecting commits ${RANGE_LABEL}..."

# Collect commits
mapfile -t COMMITS < <(git log "$RANGE" --pretty=format:"%s|%h|%an" --no-merges 2>/dev/null || git log --pretty=format:"%s|%h|%an" --no-merges)

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

# Categorize commits
for line in "${COMMITS[@]}"; do
  subject=$(echo "$line" | cut -d'|' -f1)
  hash=$(echo "$line" | cut -d'|' -f2)
  author=$(echo "$line" | cut -d'|' -f3)

  subject_lower="${subject,,}"
  entry="- ${subject} (\`${hash}\`) — ${author}"

  if echo "$subject_lower" | grep -qE '^(feat|add|new|implement|create|introduce)'; then
    ADDED+=("$entry")
  elif echo "$subject_lower" | grep -qE '^(fix|bug|patch|hotfix|resolve|correct)'; then
    FIXED+=("$entry")
  elif echo "$subject_lower" | grep -qE '^(remove|delete|deprecat|drop|clean)'; then
    REMOVED+=("$entry")
  elif echo "$subject_lower" | grep -qE '^(refactor|update|change|improve|bump|upgrade|style|perf|chore|ci|docs|build|test)'; then
    CHANGED+=("$entry")
  else
    # Try keywords anywhere in the subject
    if echo "$subject_lower" | grep -qE '\b(add|feat|new|implement)\b'; then
      ADDED+=("$entry")
    elif echo "$subject_lower" | grep -qE '\b(fix|bug|patch|resolve)\b'; then
      FIXED+=("$entry")
    elif echo "$subject_lower" | grep -qE '\b(remov|delet|deprecat|drop)\b'; then
      REMOVED+=("$entry")
    elif echo "$subject_lower" | grep -qE '\b(refactor|update|change|improve|upgrade)\b'; then
      CHANGED+=("$entry")
    else
      OTHER+=("$entry")
    fi
  fi
done

# Write CHANGELOG.md
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
  echo "and this project adheres to [Semantic Versioning](https://semver.org/)."
  echo ""
  echo "---"
  echo ""
  echo "## [${NEXT_VERSION}] — ${TODAY}"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    for item in "${ADDED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    for item in "${FIXED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    for item in "${CHANGED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    for item in "${REMOVED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#OTHER[@]} -gt 0 ]]; then
    echo "### Other"
    for item in "${OTHER[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#ADDED[@]} -eq 0 && ${#FIXED[@]} -eq 0 && ${#CHANGED[@]} -eq 0 && ${#REMOVED[@]} -eq 0 && ${#OTHER[@]} -eq 0 ]]; then
    echo "_No commits found in range: ${RANGE}_"
    echo ""
  fi

  if [[ -n "$SINCE_TAG" ]]; then
    echo "---"
    echo ""
    echo "## [${VERSION}] — Previous release"
    echo ""
    echo "_See git tags for earlier release notes._"
    echo ""
  fi
} > "$OUTPUT"

echo "✅ CHANGELOG written to: $OUTPUT"
echo "   • ${#ADDED[@]} Added"
echo "   • ${#FIXED[@]} Fixed"
echo "   • ${#CHANGED[@]} Changed"
echo "   • ${#REMOVED[@]} Removed"
echo "   • ${#OTHER[@]} Other"
