#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [repo-path]
set -euo pipefail

REPO="${1:-.}"
cd "$REPO"

# Get version from latest tag, or "Unreleased"
TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$TAG" ]; then
  VERSION="$TAG"
  RANGE="${TAG}..HEAD"
  DATE=$(git log -1 --format="%ai" "$TAG" | cut -d' ' -f1)
else
  VERSION="Unreleased"
  RANGE="HEAD"
  DATE=$(date +%Y-%m-%d)
fi

# Collect commits
declare -a ADDED FIXED CHANGED REMOVED OTHER

while IFS='|' read -r hash message; do
  # Strip conventional commit prefix, keep the rest
  clean=$(echo "$message" | sed -E 's/^(feat|fix|refactor|perf|chore|docs|style|test|ci|build)(\(.+\))?!?:\s*//')
  prefix=$(echo "$message" | sed -E 's/^([a-z]+)(\(.+\))?!?:.*/\1/')

  case "$prefix" in
    feat)     ADDED+=("- $clean ($hash)") ;;
    fix)      FIXED+=("- $clean ($hash)") ;;
    refactor|perf|chore) CHANGED+=("- $clean ($hash)") ;;
    remove|delete) REMOVED+=("- $clean ($hash)") ;;
    *)        OTHER+=("- $message ($hash)") ;;
  esac
done < <(git log --format="%h|%s" $RANGE --reverse 2>/dev/null || git log --format="%h|%s" --reverse)

# Build output
{
  echo "## [$VERSION] — $DATE"
  echo ""

  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added"
    printf '%s\n' "${ADDED[@]}"
    echo ""
  fi

  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed"
    printf '%s\n' "${FIXED[@]}"
    echo ""
  fi

  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed"
    printf '%s\n' "${CHANGED[@]}"
    echo ""
  fi

  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed"
    printf '%s\n' "${REMOVED[@]}"
    echo ""
  fi

  if [ ${#OTHER[@]} -gt 0 ]; then
    echo "### Other"
    printf '%s\n' "${OTHER[@]}"
    echo ""
  fi
}
