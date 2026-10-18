#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
# Categorizes commits since the last git tag into Added/Fixed/Changed/Removed.

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

# Determine the starting point: last tag, or root if none.
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  HEADER="## Unreleased (since ${LAST_TAG})"
else
  RANGE="HEAD"
  HEADER="## All changes"
fi

# Collect commit subjects.
mapfile -t COMMITS < <(git log "$RANGE" --pretty=format:'%s' --no-merges 2>/dev/null || true)

declare -a ADDED FIXED CHANGED REMOVED OTHER
for msg in "${COMMITS[@]}"; do
  lower="$(echo "$msg" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    feat*|add*|new*) ADDED+=("$msg") ;;
    fix*|bug*) FIXED+=("$msg") ;;
    remove*|delete*|drop*) REMOVED+=("$msg") ;;
    refactor*|update*|change*|chore*|perf*|docs*|style*|test*) CHANGED+=("$msg") ;;
    *) OTHER+=("$msg") ;;
  esac
done

{
  echo "# Changelog"
  echo ""
  echo "$HEADER"
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

echo "Generated $OUTPUT (${#COMMITS[@]} commits)"