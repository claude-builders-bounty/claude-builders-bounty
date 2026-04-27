#!/usr/bin/env bash
#
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [project-directory]
#
set -euo pipefail

# Use provided directory or current directory
PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"

# Ensure we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository. Run from a git project or specify a path." >&2
  exit 1
fi

# Find the last tag, or use the initial commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD 2>/dev/null)

if [ -z "$LAST_TAG" ]; then
  echo "Error: No commits found in this repository." >&2
  exit 1
fi

# Get the repo name
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)" 2>/dev/null || echo "project")

# Today's date
TODAY=$(date +%Y-%m-%d)

# Get version string from tag, or "0.1.0" if using initial commit
if git describe --tags --abbrev=0 > /dev/null 2>&1; then
  VERSION=$(git describe --tags --abbrev=0 2>/dev/null)
else
  VERSION="0.1.0"
fi

# Fetch all commit messages since the last tag
COMMITS=$(git log "$LAST_TAG"..HEAD --oneline --no-decorate 2>/dev/null || true)

# If no commits since tag, show all commits
if [ -z "$COMMITS" ]; then
  COMMITS=$(git log --oneline --no-decorate 2>/dev/null || true)
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
UNCATEGORIZED=""

while IFS= read -r line; do
  [ -z "$line" ] && continue
  # Remove the commit hash prefix (e.g., "abc1234 ")
  msg="${line#* }"
  # Lowercase for matching
  lc_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if echo "$lc_msg" | grep -qE '^(feat|feature|add|implement)'; then
    ADDED="$ADDED\n- $msg"
  elif echo "$lc_msg" | grep -qE '^(fix|bugfix|bug|hotfix)'; then
    FIXED="$FIXED\n- $msg"
  elif echo "$lc_msg" | grep -qE '^(refactor|chore|update|upgrade|bump)'; then
    CHANGED="$CHANGED\n- $msg"
  elif echo "$lc_msg" | grep -qE '^(remove|deprecate|delete|drop)'; then
    REMOVED="$REMOVED\n- $msg"
  else
    UNCATEGORIZED="$UNCATEGORIZED\n- $msg"
  fi
done <<< "$COMMITS"

# Build the CHANGELOG
CHANGELOG="# Changelog\n\n## [$VERSION] - $TODAY\n"

if [ -n "$(echo -e "$ADDED" | tr -d ' \n')" ]; then
  CHANGELOG="$CHANGELOG\n### Added\n$(echo -e "$ADDED")"
fi

if [ -n "$(echo -e "$FIXED" | tr -d ' \n')" ]; then
  CHANGELOG="$CHANGELOG\n### Fixed\n$(echo -e "$FIXED")"
fi

if [ -n "$(echo -e "$CHANGED" | tr -d ' \n')" ]; then
  CHANGELOG="$CHANGELOG\n### Changed\n$(echo -e "$CHANGED")"
fi

if [ -n "$(echo -e "$REMOVED" | tr -d ' \n')" ]; then
  CHANGELOG="$CHANGELOG\n### Removed\n$(echo -e "$REMOVED")"
fi

if [ -n "$(echo -e "$UNCATEGORIZED" | tr -d ' \n')" ]; then
  CHANGELOG="$CHANGELOG\n### Uncategorized\n$(echo -e "$UNCATEGORIZED")"
fi

# Write the file
echo -e "$CHANGELOG" > CHANGELOG.md
echo "✅ Generated CHANGELOG.md — $(echo "$COMMITS" | wc -l | tr -d ' ') commits categorized."
