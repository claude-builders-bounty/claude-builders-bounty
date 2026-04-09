#!/usr/bin/env bash
set -euo pipefail
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then COMMITS=$(git log "$LAST_TAG"..HEAD --oneline); else COMMITS=$(git log --oneline); fi
echo "# Changelog" > CHANGELOG.md
echo "" >> CHANGELOG.md
echo "## [Unreleased] - $(date +%Y-%m-%d)" >> CHANGELOG.md
for section in Added Fixed Changed Removed; do
  echo "### $section" >> CHANGELOG.md; echo "" >> CHANGELOG.md
  case $section in
    Added) p="feat|add|new|implement";;
    Fixed) p="fix|bug|resolve|patch";;
    Changed) p="change|update|refactor|improve";;
    Removed) p="remove|delete|drop|deprecate";;
  esac
  echo "$COMMITS" | grep -iE "$p" | while read -r line; do
    h=$(echo "$line" | awk '{print $1}'); m=$(echo "$line" | cut -d' ' -f2-)
    echo "- $m" >> CHANGELOG.md
  done
  echo "" >> CHANGELOG.md
done
echo "CHANGELOG.md generated"
