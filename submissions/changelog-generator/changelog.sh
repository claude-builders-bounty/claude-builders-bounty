#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [path/to/repo]
#        bash changelog.sh            # uses current directory

set -euo pipefail

REPO_PATH="${1:-.}"
cd "$REPO_PATH"

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository" >&2
  exit 1
fi

# Get latest tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Get version and date
if [ -n "$LATEST_TAG" ]; then
  VERSION="$LATEST_TAG"
  RANGE="$LATEST_TAG..HEAD"
else
  VERSION="Unreleased"
  RANGE="HEAD"
fi

# Get commit count
COMMIT_COUNT=$(git rev-list --count "$RANGE" 2>/dev/null || echo 0)

# Get today's date
TODAY=$(date -u +"%Y-%m-%d")

# Collect categorized commits
ADDED=$(git log "$RANGE" --pretty=format:"%s" 2>/dev/null | grep -iE '^(feat|add)[:(]' | sed 's/^/- /' || true)
FIXED=$(git log "$RANGE" --pretty=format:"%s" 2>/dev/null | grep -iE '^(fix|bug|hotfix)[:(]' | sed 's/^/- /' || true)
CHANGED=$(git log "$RANGE" --pretty=format:"%s" 2>/dev/null | grep -iE '^(refactor|perf|style|docs|chore|ci|test|build)[:(]' | sed 's/^/- /' || true)
REMOVED=$(git log "$RANGE" --pretty=format:"%s" 2>/dev/null | grep -iE '^(remove|drop|revert|deprecate)[:(]' | sed 's/^/- /' || true)

# Uncategorized commits go to Changed
UNCAT=$(git log "$RANGE" --pretty=format:"%s" 2>/dev/null | grep -viE '^(feat|add|fix|bug|hotfix|refactor|perf|style|docs|chore|ci|test|build|remove|drop|revert|deprecate|merge)[:(]' | grep -v '^$' | sed 's/^/- /' || true)

# Generate new changelog section
NEW_SECTION="## [$VERSION] - $TODAY"

if [ "$COMMIT_COUNT" -eq 0 ]; then
  NEW_SECTION="$NEW_SECTION\n\n_No changes since last release_"
else
  if [ -n "$ADDED" ]; then
    NEW_SECTION="$NEW_SECTION\n\n### Added\n$ADDED"
  fi
  if [ -n "$FIXED" ]; then
    NEW_SECTION="$NEW_SECTION\n\n### Fixed\n$FIXED"
  fi
  if [ -n "$CHANGED" ]; then
    NEW_SECTION="$NEW_SECTION\n\n### Changed\n$CHANGED"
  fi
  if [ -n "$UNCAT" ]; then
    NEW_SECTION="${NEW_SECTION}\n\n### Changed\n$UNCAT"
  fi
  if [ -n "$REMOVED" ]; then
    NEW_SECTION="$NEW_SECTION\n\n### Removed\n$REMOVED"
  fi
fi

# Check if CHANGELOG.md already exists
if [ -f "CHANGELOG.md" ]; then
  # Prepend new section after the header
  HEADER=$(head -1 CHANGELOG.md)
  REST=$(tail -n +2 CHANGELOG.md)
  
  if echo "$HEADER" | grep -q "^# Changelog"; then
    echo -e "$HEADER\n\n$NEW_SECTION\n\n$REST" > CHANGELOG.md
  else
    echo -e "# Changelog\n\n$NEW_SECTION\n\n$REST" > CHANGELOG.md
  fi
else
  echo -e "# Changelog\n\n$NEW_SECTION\n" > CHANGELOG.md
fi

echo "✅ CHANGELOG.md generated ($COMMIT_COUNT commits → $VERSION)"
cat CHANGELOG.md
