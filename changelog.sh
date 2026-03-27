#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh [output_file]
#
# Categorizes commits since the last git tag into:
#   Added / Fixed / Changed / Removed
# Falls back to all commits if no tags exist.

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || echo "project")

# Determine range: last tag to HEAD, or all commits
if LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LAST_TAG}..HEAD"
  VERSION_TAG="Unreleased"
  PREV_TAG_NOTE="since ${LAST_TAG}"
else
  RANGE="--all"
  VERSION_TAG="Unreleased"
  PREV_TAG_NOTE="(all commits)"
fi

declare -a ADDED=() FIXED=() CHANGED=() REMOVED=() OTHER=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  # Strip leading/trailing whitespace
  line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

  lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^(feat|add|added|feature)[:\(]'; then
    ADDED+=("- ${line}")
  elif echo "$lower" | grep -qE '^(fix|fixed|bugfix|hotfix)[:\(]'; then
    FIXED+=("- ${line}")
  elif echo "$lower" | grep -qE '^(chore|refactor|change|changed|update|updated|improve|improved|perf|performance|style|ci|build|docs)[:\(]'; then
    CHANGED+=("- ${line}")
  elif echo "$lower" | grep -qE '^(remove|removed|delete|deleted|deprecate|deprecated)[:\(]'; then
    REMOVED+=("- ${line}")
  else
    OTHER+=("- ${line}")
  fi
done < <(git log --oneline ${RANGE} 2>/dev/null)

# Treat conventional-commit style fixes without prefix
# Re-categorize "OTHER" into "CHANGED" if they look like regular commits
for i in "${!OTHER[@]}"; do
  CHANGED+=("${OTHER[$i]}")
done
OTHER=()

# Build the output
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to **${REPO_NAME}** ${PREV_TAG_NOTE}."
  echo ""
  echo "## ${VERSION_TAG} — $(date -u +%Y-%m-%d)"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    echo ""
    printf '%s\n' "${ADDED[@]}"
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    echo ""
    printf '%s\n' "${FIXED[@]}"
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    echo ""
    printf '%s\n' "${CHANGED[@]}"
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    echo ""
    printf '%s\n' "${REMOVED[@]}"
    echo ""
  fi

  # Preserve existing changelog sections below (if file exists)
  if [[ -f "$OUTPUT" ]]; then
    # Extract everything after the first "## Unreleased" or "##" heading
    tail -n +2 "$OUTPUT" | awk '/^## /{found=1} found{print}'
  fi
} > "$OUTPUT.tmp"

mv "$OUTPUT.tmp" "$OUTPUT"

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))
echo "✅ Generated ${OUTPUT} with ${TOTAL} entries (${PREV_TAG_NOTE})"
