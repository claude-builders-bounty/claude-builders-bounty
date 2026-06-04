#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
#   output_file defaults to CHANGELOG.md

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# ── Find the last tag ────────────────────────────────────────────────
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [ -z "$LAST_TAG" ]; then
  RANGE="HEAD"
  TAG_LABEL="(all commits — no tags found)"
else
  RANGE="${LAST_TAG}..HEAD"
  TAG_LABEL="since ${LAST_TAG}"
fi

echo "Generating changelog for commits ${TAG_LABEL}..."

# ── Collect commits ──────────────────────────────────────────────────
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=() OTHER=()

while IFS= read -r line; do
  [ -z "$line" ] && continue
  lower="$(echo "$line" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ ^(feat|add|new|added|feature) ]]; then
    ADDED+=("$line")
  elif [[ "$lower" =~ ^(fix|bug|bugfix|fixed|patch|hotfix) ]]; then
    FIXED+=("$line")
  elif [[ "$lower" =~ ^(remove|removed|delete|deleted|drop|dropped) ]]; then
    REMOVED+=("$line")
  elif [[ "$lower" =~ ^(refactor|change|changed|update|updated|chore|improve|improved|perf|perf:|style|ci|build|docs|doc|test) ]]; then
    CHANGED+=("$line")
  else
    OTHER+=("$line")
  fi
done < <(git log "$RANGE" --pretty=format:"%s" --no-merges 2>/dev/null || git log --pretty=format:"%s" --no-merges)

# ── Build the changelog ─────────────────────────────────────────────
DATE="$(date +%Y-%m-%d)"
{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased] — ${DATE} ${TAG_LABEL}"
  echo ""

  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added"
    for c in "${ADDED[@]}"; do
      echo "- ${c}"
    done
    echo ""
  fi

  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed"
    for c in "${FIXED[@]}"; do
      echo "- ${c}"
    done
    echo ""
  fi

  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed"
    for c in "${CHANGED[@]}"; do
      echo "- ${c}"
    done
    echo ""
  fi

  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed"
    for c in "${REMOVED[@]}"; do
      echo "- ${c}"
    done
    echo ""
  fi

  if [ ${#OTHER[@]} -gt 0 ]; then
    echo "### Other"
    for c in "${OTHER[@]}"; do
      echo "- ${c}"
    done
    echo ""
  fi

  # Append previous CHANGELOG content if it exists
  if [ -f "$OUTPUT" ]; then
    # Skip the first "# Changelog" header if present
    tail -n +2 "$OUTPUT" 2>/dev/null || true
  fi
} > "${OUTPUT}.tmp"

mv "${OUTPUT}.tmp" "$OUTPUT"

echo "✅ Changelog written to $OUTPUT"
echo "   Commits processed: $(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]} ))"
echo "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]} | Other: ${#OTHER[@]}"
