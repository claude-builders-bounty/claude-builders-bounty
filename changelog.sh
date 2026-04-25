#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [--since <tag|commit>] [--output <file>]
set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Determine the range: default to commits since last tag
if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi

if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..HEAD"
  RANGE_DESC="since \`${SINCE}\`"
else
  RANGE="HEAD"
  RANGE_DESC="(no previous tag — full history)"
fi

DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")
REPO_URL=$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' | sed 's|git@github.com:|https://github.com/|' || true)

# Collect commits: format = "<hash>|||<subject>"
mapfile -t COMMITS < <(git log "$RANGE" --pretty=format:"%H|||%s" --no-merges 2>/dev/null || true)

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
UNCATEGORIZED=()

categorize_commit() {
  local msg="$1"
  local lower
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  # Conventional commits: feat/add/new -> Added
  if echo "$msg" | grep -qiE '^(feat|add|new)[:(]'; then
    echo "added"
  # fix/bug/hotfix/patch -> Fixed
  elif echo "$msg" | grep -qiE '^(fix|bug|hotfix|patch)[:(]'; then
    echo "fixed"
  # remove/delete/drop/deprecate -> Removed
  elif echo "$lower" | grep -qiE '^(remove|delete|drop|deprecate)'; then
    echo "removed"
  # chore/refactor/docs/ci/build/perf/style -> Changed
  elif echo "$msg" | grep -qiE '^(chore|refactor|perf|style|test|docs|build|ci)[:(]'; then
    echo "changed"
  # Keyword-based fallbacks
  elif echo "$lower" | grep -qiE '^(add|implement|create|introduce|support)'; then
    echo "added"
  elif echo "$lower" | grep -qiE '^(fix|resolve|close|closes|closed|bug)'; then
    echo "fixed"
  elif echo "$lower" | grep -qiE '^(update|change|improve|bump|upgrade|move|rename|replace|refactor)'; then
    echo "changed"
  else
    echo "other"
  fi
}

for line in "${COMMITS[@]}"; do
  HASH="${line%%|||*}"
  MSG="${line#*|||}"
  SHORT="${HASH:0:7}"

  if [[ -n "$REPO_URL" ]]; then
    LINK="[$SHORT]($REPO_URL/commit/$HASH)"
  else
    LINK="$SHORT"
  fi

  ENTRY="- $MSG ($LINK)"
  CATEGORY=$(categorize_commit "$MSG")

  case "$CATEGORY" in
    added)   ADDED+=("$ENTRY") ;;
    fixed)   FIXED+=("$ENTRY") ;;
    changed) CHANGED+=("$ENTRY") ;;
    removed) REMOVED+=("$ENTRY") ;;
    *)       UNCATEGORIZED+=("$ENTRY") ;;
  esac
done

# Write output
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project are documented here."
  echo "Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)."
  echo ""
  echo "---"
  echo ""
  echo "## [$VERSION] — $DATE"
  echo ""
  echo "> Changes $RANGE_DESC"
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

  if [[ ${#UNCATEGORIZED[@]} -gt 0 ]]; then
    echo "### Other"
    for item in "${UNCATEGORIZED[@]}"; do echo "$item"; done
    echo ""
  fi

  if [[ ${#COMMITS[@]} -eq 0 ]]; then
    echo "_No commits found in range._"
    echo ""
  fi

} > "$OUTPUT"

echo "Generated $OUTPUT — ${#COMMITS[@]} commits categorized ($RANGE_DESC)"
