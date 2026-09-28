#!/usr/bin/env bash
# changelog.sh — generate CHANGELOG.md from git log since last tag
# Usage: ./changelog.sh [tag]  # defaults to last tag, or all commits if no tag
set -euo pipefail
TAG="${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "")}"
RANGE="${TAG:+$TAG..HEAD}"
if [ -z "$RANGE" ]; then RANGE="HEAD"; fi
echo "# Changelog"
echo ""
echo "Generated $(date -I) from $RANGE"
echo ""
for cat in Added Fixed Changed Removed; do
  echo "### $cat"
  pattern=""
  case $cat in Added) pattern="feat|add";; Fixed) pattern="fix|hotfix";; Changed) pattern="chore|refactor|perf|docs";; Removed) pattern="remove|delete|drop";; esac
  git log --pretty=format:"- %s (%h)" $RANGE 2>/dev/null | grep -i -E "$pattern" || echo "- (none)"
  echo ""
done
