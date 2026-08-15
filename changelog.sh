#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [since-tag-or-ref]
# If no arg, derives the last version tag (v* / [0-9]*.*) and uses it as the base.
set -euo pipefail

SINCE="${1:-}"
if [ -z "$SINCE" ]; then
  # last tag matching vX.Y.Z or X.Y.Z
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

RANGE="${SINCE}..HEAD"
if [ -z "$SINCE" ]; then RANGE="HEAD"; fi

echo "# Changelog"
echo ""
if [ -n "$SINCE" ]; then
  echo "## [$SINCE -> HEAD] $(date +%Y-%m-%d)"
else
  echo "## [Unreleased] $(date +%Y-%m-%d)"
fi
echo ""

declare -A seen
while IFS= read -r line; do
  hash="${line%% *}"
  msg="${line#* }"
  # skip merges and empty
  [[ "$msg" == Merge* ]] && continue
  [[ -z "$msg" ]] && continue
  # categorize by conventional-commit prefix
  case "$msg" in
    feat*:*)    grp="Added" ;;
    fix*:*)     grp="Fixed" ;;
    docs*:*)    grp="Docs" ;;
    refactor*:*)grp="Changed" ;;
    perf*:*)    grp="Changed" ;;
    test*:*)    grp="Tests" ;;
    chore*:*)   grp="Chore" ;;
    *)          grp="Other" ;;
  esac
  printf -- "- %s (%s)\n" "$msg" "$hash" >> "/tmp/cl_$grp"
done < <(git log --pretty="%h %s" "$RANGE")

for g in Added Fixed Changed Docs Tests Chore Other; do
  f="/tmp/cl_$g"
  if [ -f "$f" ]; then
    echo "### $g"
    cat "$f"
    echo ""
    rm -f "$f"
  fi
done
