#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
#
# Acceptance (bounty): fetch commits since the last git tag, auto-categorize
# into Added / Fixed / Changed / Removed, emit a properly formatted CHANGELOG.md.
#
# Conventions recognized (case-insensitive prefix on the subject line):
#   feat|add|new         -> Added
#   fix|bug|patch        -> Fixed
#   refactor|perf|chore|style|docs|test|build|ci|deps -> Changed
#   remove|drop|delete   -> Removed
# Unknown subjects land under Changed (safe default, never dropped).
#
# Usage:
#   bash changelog.sh              # CHANGELOG.md in the current repo
#   bash changelog.sh v1.0.0       # from a specific tag
#   bash changelog.sh v1.0.0..HEAD # from a specific range
set -euo pipefail

RANGE="${1:-}"

# Resolve the commit range. Default: commits since the most recent tag.
if [[ -z "$RANGE" ]]; then
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$LAST_TAG" ]]; then
    RANGE="${LAST_TAG}..HEAD"
  else
    RANGE="HEAD"
  fi
fi

OUT="${CHANGELOG_FILE:-CHANGELOG.md}"

categorize() {
  # categorize <subject> -> section name (Added|Fixed|Changed|Removed)
  local s="$1"
  case "$s" in
    feat*|add*|new*|implement*) echo "Added" ;;
    fix*|bug*|patch*|hotfix*|repair*) echo "Fixed" ;;
    remove*|drop*|delete*|deprecate*) echo "Removed" ;;
    *) echo "Changed" ;;
  esac
}

# Build the changelog in memory: an ordered map section -> list of "hash subject".
declare -A SECTIONS=()
ORDER=(Added Fixed Changed Removed)

while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" ]] && continue
  hash="${line%%|*}"
  subject="${line#*|}"
  sec="$(categorize "${subject,,}")"
  SECTIONS["$sec"]+="${SECTIONS[$sec]:+$'\n'}  - ${subject} (${hash})"
done < <(git log "$RANGE" --no-merges --pretty=format:'%h|%s' 2>/dev/null || true)

{
  echo "# Changelog"
  echo
  echo "Generated $(date -u +%Y-%m-%d) from git history (${RANGE})."
  echo
  for sec in "${ORDER[@]}"; do
    if [[ -n "${SECTIONS[$sec]:-}" ]]; then
      echo "## ${sec}"
      echo "${SECTIONS[$sec]}"
      echo
    fi
  done
} > "$OUT"

N=$(grep -c '^  - ' "$OUT" 2>/dev/null || true)
echo "Wrote ${N:-0} entries to $OUT"
