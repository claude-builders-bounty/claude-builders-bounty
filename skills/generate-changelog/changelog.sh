#!/bin/bash
# /generate-changelog — Auto-generate structured CHANGELOG.md from git history
# Bounty: claude-builders-bounty #1

set -euo pipefail

REPO=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "project")
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
  echo "No git tags found. Using first commit as baseline."
  LAST_TAG=$(git rev-list --max-parents=0 HEAD)
  RANGE="$LAST_TAG..HEAD"
else
  RANGE="$LAST_TAG..HEAD"
fi

echo "# Changelog" > CHANGELOG.md
echo "" >> CHANGELOG.md
echo "## [Unreleased] — $(date +%Y-%m-%d)" >> CHANGELOG.md
echo "" >> CHANGELOG.md

ADDED=$(git log "$RANGE" --no-merges --pretty=format:"- %s (%h)" --grep="^feat:\|^add:\|^new:\|^Added" 2>/dev/null)
FIXED=$(git log "$RANGE" --no-merges --pretty=format:"- %s (%h)" --grep="^fix:\|^bug:\|^patch:\|resolve\|close" 2>/dev/null)
CHANGED=$(git log "$RANGE" --no-merges --pretty=format:"- %s (%h)" --grep="^refactor:\|^update:\|^tweak:\|^perf:\|^style:" 2>/dev/null)
REMOVED=$(git log "$RANGE" --no-merges --pretty=format:"- %s (%h)" --grep="^remove:\|^delete:\|^drop:\|^deprecate:" 2>/dev/null)
UNCAT=$(git log "$RANGE" --no-merges --pretty=format:"- %s (%h)" --grep="^feat:\|^fix:\|^refactor:\|^remove:\|^add:\|^bug:\|^update:\|^new:\|^delete:\|^drop:\|^patch:\|^tweak:\|^perf:\|^style:\|^deprecate:\|resolve\|close" --invert-grep 2>/dev/null)

section() {
  if [ -n "${2:-}" ]; then
    echo "### $1" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
    echo "$2" >> CHANGELOG.md
    echo "" >> CHANGELOG.md
  fi
}

section "Added" "$ADDED"
section "Fixed" "$FIXED"
section "Changed" "$CHANGED"
section "Removed" "$REMOVED"
section "Other" "$UNCAT"

COMMIT_COUNT=$(git rev-list --count "$RANGE" 2>/dev/null || echo 0)
PREV_TAG_LINK="[$LAST_TAG]: ../${LAST_TAG//v/}"
echo "" >> CHANGELOG.md
echo "[Unreleased]: ." >> CHANGELOG.md

echo "CHANGELOG.md generated — $COMMIT_COUNT commits since $LAST_TAG"
echo "Preview:"
head -20 CHANGELOG.md
