#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   cd /path/to/your/repo
#   bash changelog.sh             # writes CHANGELOG.md
#   bash changelog.sh -o RELEASE  # output to RELEASE.md
#
# Categorizes commits by conventional-commit type:
#   feat       → Added
#   fix        → Fixed
#   remove     → Removed
#   everything → Changed (chore, refactor, docs, style, perf, test, ci, build, breaking)
#
set -euo pipefail

OUTPUT="CHANGELOG.md"
while getopts "ho:" opt; do
  case "$opt" in
    h) sed -n '4,12p' "$0"; exit 0 ;;
    o) OUTPUT="$OPTARG" ;;
    *) exit 1 ;;
  esac
done

# ── Detect last tag ─────────────────────────────────────────────────
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [ -z "$LAST_TAG" ]; then
  SINCE=$(git rev-list --max-parents=0 HEAD)
  NEW_TAG="0.1.0"
else
  SINCE="$LAST_TAG"
  IFS='.' read -r MAJOR MINOR PATCH <<< "${LAST_TAG#v}"
  MAJOR=${MAJOR:-0}; MINOR=${MINOR:-1}; PATCH=${PATCH:-0}
  NEW_TAG="${MAJOR}.${MINOR}.$((PATCH + 1))"
fi

# ── Collect commits as JSON lines (safe delimiter) ──────────────────
COMMITS=$(git log "$SINCE..HEAD" --pretty=format:'%x1f%s%x1f%h%x1f%aI%x1e' --no-merges 2>/dev/null || true)
if [ -z "$COMMITS" ]; then
  echo "No new commits since $SINCE."
  exit 0
fi

# ── Categorize ──────────────────────────────────────────────────────
ADDED=(); FIXED=(); CHANGED=(); REMOVED=()

while IFS=$'\x1f' read -r _raw SUBJECT HASH DATE _rest; do
  [ -z "$SUBJECT" ] && continue
  LOW=$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')

  if echo "$LOW" | grep -qE '^feat(\([^)]*\))?!?\s*:'; then
    CAT="added"
  elif echo "$LOW" | grep -qE '^fix(\([^)]*\))?!?\s*:'; then
    CAT="fixed"
  elif echo "$LOW" | grep -qE '^(remove|deprecate)(\([^)]*\))?!?\s*:'; then
    CAT="removed"
  else
    CAT="changed"
  fi

  CLEAN=$(echo "$SUBJECT" | sed -E 's/^(feat|fix|chore|docs|refactor|style|perf|test|ci|build|remove|deprecate)(\([^)]*\))?!?\s*:\s*//i')
  SHORT_DATE=$(echo "$DATE" | cut -dT -f1)

  case "$CAT" in
    added)   ADDED+=("* $CLEAN ($HASH, $SHORT_DATE)") ;;
    fixed)   FIXED+=("* $CLEAN ($HASH, $SHORT_DATE)") ;;
    removed) REMOVED+=("* $CLEAN ($HASH, $SHORT_DATE)") ;;
    *)       CHANGED+=("* $CLEAN ($HASH, $SHORT_DATE)") ;;
  esac
done < <(printf '%s' "$COMMITS" | tr $'\x1e' '\n' | sed '/^$/d')

# ── Render ──────────────────────────────────────────────────────────
TODAY=$(date +%Y-%m-%d)
{
  echo "# Changelog"
  echo
  echo "## [$NEW_TAG] — $TODAY"
  echo
  [ ${#ADDED[@]} -gt 0 ]   && { echo "### Added";    for e in "${ADDED[@]}";   do echo "$e"; done; echo; }
  [ ${#FIXED[@]} -gt 0 ]   && { echo "### Fixed";    for e in "${FIXED[@]}";   do echo "$e"; done; echo; }
  [ ${#CHANGED[@]} -gt 0 ] && { echo "### Changed";  for e in "${CHANGED[@]}"; do echo "$e"; done; echo; }
  [ ${#REMOVED[@]} -gt 0 ] && { echo "### Removed";  for e in "${REMOVED[@]}"; do echo "$e"; done; echo; }
  TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))
  [ "$TOTAL" -eq 0 ] && echo "_No significant changes._" && echo
} > "$OUTPUT"

echo "Wrote $OUTPUT ($TOTAL commits across $(ls "$OUTPUT" && echo -n "${#CHANGED[@]} changed, ${#ADDED[@]} added, ${#FIXED[@]} fixed, ${#REMOVED[@]} removed"))"
