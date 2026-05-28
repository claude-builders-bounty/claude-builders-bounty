#!/usr/bin/env bash
set -euo pipefail

OUT=${1:-CHANGELOG.md}
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
  SINCE="since $LAST_TAG"
else
  RANGE="HEAD"
  SINCE="for entire history"
fi

map_commits() {
  local pattern=$1
  git log "$RANGE" --no-merges --pretty=format:'%s (%h)' 2>/dev/null \
    | awk -v pat="$pattern" 'BEGIN{IGNORECASE=1} $0 ~ pat {print "- " $0}'
}

ADDED=$(map_commits '^(feat|add|create|implement)(\(.+\))?:|add|new|implement')
FIXED=$(map_commits '^(fix|bugfix|hotfix)(\(.+\))?:|fix|bug|error|crash')
CHANGED=$(map_commits '^(change|refactor|perf|docs|style|test|chore)(\(.+\))?:|change|update|refactor|improve')
REMOVED=$(map_commits '^(remove|delete|drop)(\(.+\))?:|remove|delete|drop|deprecat')

uncategorized=$(git log "$RANGE" --no-merges --pretty=format:'%s (%h)' 2>/dev/null \
  | awk 'BEGIN{IGNORECASE=1} $0 !~ /^(feat|add|create|implement|fix|bugfix|hotfix|change|refactor|perf|docs|style|test|chore|remove|delete|drop)(\(.+\))?:|add|new|implement|fix|bug|error|crash|change|update|refactor|improve|remove|delete|drop|deprecat/ {print "- " $0}')
[ -z "$CHANGED" ] && CHANGED=$uncategorized

date_utc=$(date -u +%Y-%m-%d)
{
  echo "# Changelog"
  echo
  echo "## Unreleased - $date_utc"
  echo
  echo "Generated from commits $SINCE."
  echo
  echo "### Added";   [ -n "$ADDED" ] && echo "$ADDED" || echo "- No notable additions."
  echo
  echo "### Fixed";   [ -n "$FIXED" ] && echo "$FIXED" || echo "- No notable fixes."
  echo
  echo "### Changed"; [ -n "$CHANGED" ] && echo "$CHANGED" || echo "- No notable changes."
  echo
  echo "### Removed"; [ -n "$REMOVED" ] && echo "$REMOVED" || echo "- No notable removals."
} > "$OUT"

echo "Wrote $OUT ($SINCE)"
