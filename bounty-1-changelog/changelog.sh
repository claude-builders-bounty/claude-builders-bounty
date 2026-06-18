#!/usr/bin/env bash
# generate-changelog — build a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>]
#
# Fetches all commits since the last git tag (or the full history if no tags),
# auto-categorizes them, and writes a Keep-a-Changelog-compatible CHANGELOG.md.

set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE_TAG=""

# ── argument parsing ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE_TAG="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ── detect range ─────────────────────────────────────────────────────────────
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  SINCE_DESC="since \`${SINCE_TAG}\`"
else
  RANGE="HEAD"
  SINCE_DESC="full history"
fi

VERSION=$(git describe --tags --abbrev=0 HEAD 2>/dev/null || echo "Unreleased")
DATE=$(date +%Y-%m-%d)

# ── fetch commits ─────────────────────────────────────────────────────────────
# Format: subject only, one per line
COMMITS=$(git log "$RANGE" --no-merges --pretty=format:"%s" 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "No commits found for range: $RANGE" >&2
  exit 0
fi

# ── categorize ───────────────────────────────────────────────────────────────
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  lower="${line,,}"
  case "$lower" in
    feat*|add*|new*|implement*|create*)   ADDED+=("$line") ;;
    fix*|bug*|patch*|resolve*|correct*)   FIXED+=("$line") ;;
    refactor*|update*|change*|improve*|perf*|style*|chore*|ci*|build*|docs*) CHANGED+=("$line") ;;
    remove*|delete*|drop*|deprecat*)      REMOVED+=("$line") ;;
    *)                                    OTHER+=("$line") ;;
  esac
done <<< "$COMMITS"

# ── write output ──────────────────────────────────────────────────────────────
{
  echo "# Changelog"
  echo ""
  echo "All notable changes are documented here ($SINCE_DESC)."
  echo ""
  echo "## [$VERSION] — $DATE"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    for c in "${ADDED[@]}"; do echo "- $c"; done
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    for c in "${FIXED[@]}"; do echo "- $c"; done
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    for c in "${CHANGED[@]}"; do echo "- $c"; done
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    for c in "${REMOVED[@]}"; do echo "- $c"; done
    echo ""
  fi

  if [[ ${#OTHER[@]} -gt 0 ]]; then
    echo "### Other"
    for c in "${OTHER[@]}"; do echo "- $c"; done
    echo ""
  fi
} > "$OUTPUT"

echo "✓ Written to $OUTPUT (${#ADDED[@]} added, ${#FIXED[@]} fixed, ${#CHANGED[@]} changed, ${#REMOVED[@]} removed, ${#OTHER[@]} other)"
