#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history.
# Bounty #1: $50 — claude-builders-bounty
#
# Usage:
#   bash changelog.sh                 # write CHANGELOG.md in current repo
#   bash changelog.sh -o out.md       # write to custom path
#   bash changelog.sh -v              # show commits categorized (dry run)
#
# Behavior:
#   - Fetches commits since the last git tag (falls back to first commit)
#   - Auto-categorizes into Added / Fixed / Changed / Removed via keyword rules
#   - Emits Keep-a-Changelog style output
set -eo pipefail

OUT="CHANGELOG.md"
VERBOSE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output) OUT="$2"; shift 2 ;;
    -v|--verbose) VERBOSE=1; shift ;;
    *) echo "Unknown option: $1" >&2; echo "Usage: bash changelog.sh [-o out.md] [-v]" >&2; exit 1 ;;
  esac
done

# 1. Find the range: commits since last tag, else entire history.
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  VERSION_STR="Unreleased (since ${LAST_TAG})"
else
  RANGE="HEAD"
  VERSION_STR="Unreleased"
fi

# 2. Categorize each commit by its subject prefix (plain vars, bash-3.2 safe).
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  subject="${line#* }"                 # strip hash
  low=$(echo "$subject" | tr 'A-Z' 'a-z')
  case "$low" in
    fix:*|fix\(*|bugfix:*|hotfix:*|bug:*)
      FIXED="${FIXED}- ${subject}"$'\n' ;;
    feat:*|feature:*|add:*|add\(*|new:*|implement*|support:*)
      ADDED="${ADDED}- ${subject}"$'\n' ;;
    remove:*|drop:*|delete:*|deprecate:*|rm\ *)
      REMOVED="${REMOVED}- ${subject}"$'\n' ;;
    refactor:*|update:*|upgrade:*|bump:*|change:*|perf:*|improve:*|migrate:*|rework:*)
      CHANGED="${CHANGED}- ${subject}"$'\n' ;;
    *)
      CHANGED="${CHANGED}- ${subject}"$'\n' ;;   # default bucket
  esac
done < <(git log --oneline --no-merges "$RANGE")

# 3. Render.
{
  echo "# Changelog"
  echo
  echo "## ${VERSION_STR}"
  echo
  if [[ -n "$ADDED" ]]; then echo "### Added"; echo; printf '%s' "$ADDED"; echo; fi
  if [[ -n "$FIXED" ]]; then echo "### Fixed"; echo; printf '%s' "$FIXED"; echo; fi
  if [[ -n "$CHANGED" ]]; then echo "### Changed"; echo; printf '%s' "$CHANGED"; echo; fi
  if [[ -n "$REMOVED" ]]; then echo "### Removed"; echo; printf '%s' "$REMOVED"; echo; fi
} > "$OUT"

COUNT=$(git log --oneline --no-merges "$RANGE" | wc -l | tr -d ' ')
echo "✓ CHANGELOG.md written (${COUNT} commits categorized)" >&2
[[ "$VERBOSE" == 1 ]] && cat "$OUT"
