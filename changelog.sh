#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Fetches commits since the last git tag, auto-categorizes them into
# Added / Fixed / Changed / Removed (based on Conventional Commits prefixes
# and common keywords), and writes a properly formatted CHANGELOG.md.
#
# Usage:
#   ./changelog.sh [--since <ref>] [--out CHANGELOG.md] [--version vX.Y.Z]
#
# Exit codes:
#   0  success
#   1  not a git repository or no commits

set -euo pipefail

OUT="CHANGELOG.md"
SINCE=""
VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="${2:-}"; shift 2 ;;
    --out)   OUT="${2:-}"; shift 2 ;;
    --version) VERSION="${2:-}"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not a git repository" >&2
  exit 1
fi

# Determine the range: from last tag (or first commit) up to HEAD.
if [[ -z "$SINCE" ]]; then
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$LAST_TAG" ]]; then
    SINCE="$LAST_TAG"
    RANGE="${LAST_TAG}..HEAD"
  else
    FIRST_COMMIT="$(git rev-list --max-parents=0 HEAD 2>/dev/null | head -n1)"
    SINCE="${FIRST_COMMIT}"
    RANGE="${FIRST_COMMIT}..HEAD"
  fi
else
  RANGE="${SINCE}..HEAD"
fi

VERSION_LABEL="${VERSION:-Unreleased}"
DATE="$(date +%Y-%m-%d)"

# Collect subject lines only (one per commit), newest first.
mapfile -t COMMITS < <(git log "${RANGE}" --pretty=format:'%s' 2>/dev/null)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  echo "No commits found in range ${RANGE}." >&2
  exit 1
fi

categorize() {
  local msg="$1"
  local lower="$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    fix*:*|*fix*bug*|*hotfix*) printf 'Fixed' ;;
    feat*:|*add*|*new*|*support*|*introduce*) printf 'Added' ;;
    remove*:|*delete*|*drop*|*deprecate*) printf 'Removed' ;;
    *) printf 'Changed' ;;
  esac
}

declare -a ADDED=() FIXED=() CHANGED=() REMOVED=()

for msg in "${COMMITS[@]}"; do
  # Strip a leading "type:" conventional-commits prefix for cleaner display.
  clean="$(printf '%s' "$msg" | sed -E 's/^[a-z]+(\([^)]*\))?!?:[[:space:]]*//I')"
  [[ -z "$clean" ]] && clean="$msg"
  cat="$(categorize "$msg")"
  case "$cat" in
    Added)   ADDED+=("$clean") ;;
    Fixed)   FIXED+=("$clean") ;;
    Removed) REMOVED+=("$clean") ;;
    *)       CHANGED+=("$clean") ;;
  esac
done

emit() {
  local title="$1"
  local -n arr="$2"
  if [[ ${#arr[@]} -gt 0 ]]; then
    echo "### $title"
    echo
    for item in "${arr[@]}"; do
      echo "- $item"
    done
    echo
  fi
}

{
  echo "# Changelog"
  echo
  echo "## [$VERSION_LABEL] - $DATE"
  echo
  echo "> Generated from ${SINCE}..HEAD (${#COMMITS[@]} commits)"
  echo
  emit "Added" ADDED
  emit "Changed" CHANGED
  emit "Fixed" FIXED
  emit "Removed" REMOVED
} > "$OUT"

echo "Wrote $OUT (${#COMMITS[@]} commits categorized)."
