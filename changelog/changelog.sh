#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh [output-file]   # default CHANGELOG.md
#
# Collects commits since the most recent git tag (or all commits when
# the repo has none) and buckets them into Added / Fixed / Changed /
# Removed using the subject prefix or conventional-commit type.
set -euo pipefail

OUT="${1:-CHANGELOG.md}"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  VERSION="Unreleased"
else
  RANGE="HEAD"
  VERSION="Unreleased"
fi

ADDED=(); FIXED=(); CHANGED=(); REMOVED=(); OTHER=()

while IFS= read -r line; do
  [ -z "$line" ] && continue
  msg="${line#* }"
  lower="$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')"
  clean="$(printf '%s' "$msg" | sed -E 's/^(feat|fix|chore|docs|refactor|perf|style|test|build|ci|revert)(\([^)]*\))?!?: *//I')"
  case "$lower" in
    feat*|*feature*|add\ *|added\ *|adds\ *|implement*|introduc*|support\ *) ADDED+=("$clean") ;;
    fix*|bugfix*|hotfix*|patch*|resolve*|correct*|repair*) FIXED+=("$clean") ;;
    remove*|drop\ *|delete*|deprecat*|revert*) REMOVED+=("$clean") ;;
    chang*|updat*|upgrad*|refactor*|improv*|optimiz*|bump*|perf*|enhanc*|migrat*|renam*) CHANGED+=("$clean") ;;
    *) OTHER+=("$clean") ;;
  esac
done < <(git log "$RANGE" --pretty=format:'%h %s' --no-merges; echo)

{
  echo "# Changelog"
  echo
  echo "All notable changes to this project will be documented in this file."
  echo
  echo "## [$VERSION] - $(date +%Y-%m-%d)"
  if [ -n "$LAST_TAG" ]; then
    echo
    echo "Changes since $LAST_TAG."
  fi
  section() {
    local title="$1"; shift
    local -n arr=$1
    [ "${#arr[@]}" -eq 0 ] && return 0
    echo
    echo "### $title"
    for item in "${arr[@]}"; do
      echo "- $item"
    done
  }
  section Added ADDED
  section Fixed FIXED
  section Changed CHANGED
  section Removed REMOVED
  section Other OTHER
} > "$OUT"

echo "Wrote $OUT ($(git rev-list --count "$RANGE" --no-merges 2>/dev/null || echo 0) commits since ${LAST_TAG:-repo start})"
