#!/usr/bin/env bash
set -euo pipefail

# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [-o output] [-t tag] [-a] [-s]

VERSION="1.0.0"
OUTPUT="CHANGELOG.md"
START_TAG=""
ALL=false
SUMMARY=false

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Generate a structured CHANGELOG.md from git history.

Options:
  -o FILE   Output file (default: CHANGELOG.md)
  -t TAG    Start from this tag (default: latest tag)
  -a        Include all history (not just since last tag)
  -s        Summary mode — one line per commit
  -h        Show this help
  -v        Show version
EOF
  exit 0
}

while getopts "o:t:ashv" opt; do
  case "$opt" in
    o) OUTPUT="$OPTARG" ;;
    t) START_TAG="$OPTARG" ;;
    a) ALL=true ;;
    s) SUMMARY=true ;;
    h) usage ;;
    v) echo "changelog.sh $VERSION"; exit 0 ;;
    *) usage ;;
  esac
done

# Ensure we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not a git repository" >&2
  exit 1
fi

REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
TODAY=$(date '+%Y-%m-%d')

# Determine the starting point
if [ -n "$START_TAG" ]; then
  RANGE="$START_TAG..HEAD"
elif $ALL; then
  RANGE=""
else
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [ -n "$LATEST_TAG" ]; then
    RANGE="$LATEST_TAG..HEAD"
  else
    RANGE=""
  fi
fi

# Categorize a commit message
categorize() {
  local msg="$1"
  local lower
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  case "$lower" in
    feat:*|feat\(*\):*|add:*|added:*|added\(*\):*) echo "ADDED" ;;
    fix:*|fix\(*\):*|bug:*|bugfix:*|hotfix:*|patch:*) echo "FIXED" ;;
    remove:*|removed:*|deprecate:*|deprecated:*|delete:*|deleted:*|drop:*|dropped:*) echo "REMOVED" ;;
    change:*|changed:*|refactor:*|refactored:*|chore:*|docs:*|doc:*|style:*|ci:*|build:*|perf:*|test:*) echo "CHANGED" ;;
    *) echo "CHANGED" ;;
  esac
}

# Collect commits
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

if [ -z "$RANGE" ]; then
  COMMIT_LIST=$(git log --pretty=format:"%s" --reverse)
else
  COMMIT_LIST=$(git log --pretty=format:"%s" --reverse "$RANGE")
fi

if [ -z "$COMMIT_LIST" ]; then
  echo "No commits found in range. Nothing to generate."
  exit 0
fi

while IFS= read -r msg; do
  [ -z "$msg" ] && continue
  case "$(categorize "$msg")" in
    ADDED)   ADDED+=("$msg") ;;
    FIXED)   FIXED+=("$msg") ;;
    REMOVED) REMOVED+=("$msg") ;;
    CHANGED) CHANGED+=("$msg") ;;
  esac
done <<< "$COMMIT_LIST"

# Generate output
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "## [Unreleased] - $TODAY"
  echo ""

  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added"
    for c in "${ADDED[@]}"; do
      echo "- $c"
    done
    echo ""
  fi

  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed"
    for c in "${FIXED[@]}"; do
      echo "- $c"
    done
    echo ""
  fi

  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed"
    for c in "${CHANGED[@]}"; do
      echo "- $c"
    done
    echo ""
  fi

  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed"
    for c in "${REMOVED[@]}"; do
      echo "- $c"
    done
    echo ""
  fi
} > "$OUTPUT"

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))
echo "✅ Generated $OUTPUT ($TOTAL commits categorized: +${#ADDED[@]} added, ~${#FIXED[@]} fixed, ~${#CHANGED[@]} changed, -${#REMOVED[@]} removed)"
