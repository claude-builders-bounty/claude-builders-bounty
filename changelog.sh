#!/bin/bash
# CHANGELOG Generator — generates CHANGELOG.md from git history
# macOS compatible (Bash 3.2+)

set -e

echo "# Changelog" > CHANGELOG.md
echo "" >> CHANGELOG.md

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [[ -n "$LAST_TAG" ]]; then
  echo "## [$LAST_TAG] ($(date +%Y-%m-%d))" >> CHANGELOG.md
  COMMITS=$(git log "$LAST_TAG..HEAD" --oneline --format='%s')
else
  echo "## [Unreleased] ($(date +%Y-%m-%d))" >> CHANGELOG.md
  COMMITS=$(git log --oneline --format='%s')
fi

added=""
fixed=""
changed=""
removed=""

while IFS= read -r commit; do
  lc=$(echo "$commit" | tr '[:upper:]' '[:lower:]')
  cat="Changed"
  
  if echo "$lc" | grep -qE "^(新增|添加|feat|add)"; then
    cat="Added"
  elif echo "$lc" | grep -qE "^(fix|修复|bugfix)"; then
    cat="Fixed"
  elif echo "$lc" | grep -qE "^(remove|删除|remove|deprecated)"; then
    cat="Removed"
  fi
  
  case "$cat" in
    Added)   added="$added- $commit"$'\n' ;;
    Fixed)   fixed="$fixed- $commit"$'\n' ;;
    Removed) removed="$removed- $commit"$'\n' ;;
    Changed) changed="$changed- $commit"$'\n' ;;
  esac
done <<< "$COMMITS"

if [[ -n "$added" ]]; then
  echo "### Added" >> CHANGELOG.md
  echo -e "$added" >> CHANGELOG.md
fi
if [[ -n "$fixed" ]]; then
  echo "### Fixed" >> CHANGELOG.md
  echo -e "$fixed" >> CHANGELOG.md
fi
if [[ -n "$changed" ]]; then
  echo "### Changed" >> CHANGELOG.md
  echo -e "$changed" >> CHANGELOG.md
fi
if [[ -n "$removed" ]]; then
  echo "### Removed" >> CHANGELOG.md
  echo -e "$removed" >> CHANGELOG.md
fi

echo "" >> CHANGELOG.md
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')" >> CHANGELOG.md
echo "" >> CHANGELOG.md
cat CHANGELOG.md
