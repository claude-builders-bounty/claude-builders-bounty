#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   ./changelog.sh              # commits since last tag → CHANGELOG.md
#   ./changelog.sh --stdout     # print to stdout instead
#   ./changelog.sh v1.0..HEAD   # explicit range
#
# Auto-categorises by conventional-commit prefix:
#   feat/add    → Added
#   fix/bug     → Fixed
#   remove      → Removed
#   other       → Changed

set -euo pipefail

STDOUT=false
if [[ "${1:-}" == "--stdout" ]]; then
  STDOUT=true
  shift
fi

# ── Determine commit range ──────────────────────────────────────────────
if [[ $# -ge 1 ]]; then
  RANGE="$1"
else
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LATEST_TAG" ]]; then
    RANGE="${LATEST_TAG}..HEAD"
  else
    RANGE=""
  fi
fi

# ── Fetch commits ───────────────────────────────────────────────────────
if [[ -n "$RANGE" ]]; then
  COMMITS=$(git log --format="%h|%s" "$RANGE" 2>/dev/null || true)
else
  COMMITS=$(git log --format="%h|%s" 2>/dev/null || true)
fi

if [[ -z "$COMMITS" ]]; then
  echo "⚠️  No commits found for range: ${RANGE:-all history}" >&2
  exit 0
fi

# ── Categorise ──────────────────────────────────────────────────────────
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS='|' read -r hash subject; do
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
  entry="- ${subject} (\`${hash}\`)"

  case "$lower" in
    feat\ *|feat\:*|feat\(*|add\ *|add\:*|add\.*|add\(*)
      ADDED+="$entry"$'\n' ;;
    fix\ *|fix\:*|fix\(*|bug\ *|bug\:*|bug\(*)
      FIXED+="$entry"$'\n' ;;
    remov*)
      REMOVED+="$entry"$'\n' ;;
    chore\ *|chore\:*|style\ *|style\:*|docs\ *|docs\:*|test\ *|test\:*|ci\ *|ci\:*|build\ *|build\:*)
      ;; # skip housekeeping
    *)
      CHANGED+="$entry"$'\n' ;;
  esac
done <<< "$COMMITS"

# ── Build markdown ──────────────────────────────────────────────────────
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
DATE=$(date +%Y-%m-%d)
VERSION="${RANGE:-all history}"

{
  echo "# CHANGELOG — ${PROJECT}"
  echo ""
  echo "## [${VERSION}] — ${DATE}"
  echo ""

  [[ -n "$ADDED" ]]   && { echo "### Added";   echo "$ADDED";   echo ""; }
  [[ -n "$FIXED" ]]   && { echo "### Fixed";   echo "$FIXED";   echo ""; }
  [[ -n "$CHANGED" ]] && { echo "### Changed"; echo "$CHANGED"; echo ""; }
  [[ -n "$REMOVED" ]] && { echo "### Removed"; echo "$REMOVED"; echo ""; }

  if [[ -z "$ADDED" && -z "$FIXED" && -z "$CHANGED" && -z "$REMOVED" ]]; then
    echo "### Other"
    while IFS='|' read -r hash subject; do
      echo "- ${subject} (\`${hash}\`)"
    done <<< "$COMMITS"
    echo ""
  fi
} > /tmp/_changelog_tmp.md

# ── Output ──────────────────────────────────────────────────────────────
if [[ "$STDOUT" == true ]]; then
  cat /tmp/_changelog_tmp.md
else
  mv /tmp/_changelog_tmp.md CHANGELOG.md
  echo "✅ CHANGELOG.md written ($(wc -l < CHANGELOG.md) lines)"
fi
