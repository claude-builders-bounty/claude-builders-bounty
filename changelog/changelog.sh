#!/usr/bin/env bash
#
# changelog.sh — generate a structured CHANGELOG.md from a project's git history.
#
# Usage:
#   bash changelog.sh [repo_path]
#
# Behavior:
#   - Fetches all commits since the last git tag (or the full history if no tags exist).
#   - Auto-categorizes commits into Added / Fixed / Changed / Removed based on
#     conventional-commit prefixes (feat, fix, perf, refactor, ...) with keyword
#     fallbacks (remove/deprecate/delete => Removed).
#   - Writes a properly formatted CHANGELOG.md in the repo root.
#
set -euo pipefail

REPO="${1:-.}"
OUT="$REPO/CHANGELOG.md"

LAST_TAG="$(git -C "$REPO" describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  VERSION="$LAST_TAG"
else
  RANGE="HEAD"
  VERSION="$(git -C "$REPO" rev-parse --short HEAD)"
fi

COMMITS="$(git -C "$REPO" log --pretty=format:'%h|%s' "$RANGE" 2>/dev/null || true)"
if [ -z "$COMMITS" ]; then
  echo "No commits found after ${LAST_TAG:-'the beginning'}." >&2
  exit 1
fi

classify() {
  local lower
  lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    feat*|feature*)            echo "Added" ;;
    fix*|bug*|hotfix*)         echo "Fixed" ;;
    perf*|refactor*|style*|docs*|doc*|test*|build*|ci*|chore*|revert*|maintenance*)
                               echo "Changed" ;;
    *)
      case "$lower" in
        *remov*|*deprecat*|*delet*) echo "Removed" ;;
        *)                          echo "Changed" ;;
      esac
      ;;
  esac
}

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS='|' read -r hash subj; do
  [ -z "$hash" ] && continue
  case "$(classify "$subj")" in
    Added)   ADDED+="- ${subj} (${hash})"$'\n' ;;
    Fixed)   FIXED+="- ${subj} (${hash})"$'\n' ;;
    Removed) REMOVED+="- ${subj} (${hash})"$'\n' ;;
    *)       CHANGED+="- ${subj} (${hash})"$'\n' ;;
  esac
done <<< "$COMMITS"

DATE="$(date +%Y-%m-%d)"

{
  echo "# Changelog"
  echo
  echo "All notable changes to this project are documented in this file."
  echo
  echo "## ${VERSION} (${DATE})"
  [ -n "$ADDED" ]   && { echo; echo "### Added";   printf '%s' "$ADDED"; }
  [ -n "$FIXED" ]   && { echo; echo "### Fixed";   printf '%s' "$FIXED"; }
  [ -n "$CHANGED" ] && { echo; echo "### Changed"; printf '%s' "$CHANGED"; }
  [ -n "$REMOVED" ] && { echo; echo "### Removed"; printf '%s' "$REMOVED"; }
} > "$OUT"

COUNT=$(printf '%s\n' "$COMMITS" | grep -c '|' || true)
echo "Wrote $OUT (${VERSION}, $COUNT commits)"
