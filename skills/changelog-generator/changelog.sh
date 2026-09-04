#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [--from-tag TAG] [--to-ref REF] [--output FILE]
#
# Examples:
#   ./changelog.sh                          # since last tag → stdout
#   ./changelog.sh --from-tag v1.0.0        # since v1.0.0
#   ./changelog.sh -o CHANGELOG.md          # write to file
#   ./changelog.sh --from-tag v1.0.0 -o CHANGELOG.md

set -euo pipefail

# --- Defaults ---
FROM_TAG=""
TO_REF="HEAD"
OUTPUT_FILE=""
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo '.')"

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from-tag) FROM_TAG="$2"; shift 2 ;;
    --to-ref)   TO_REF="$2"; shift 2 ;;
    -o|--output) OUTPUT_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--from-tag TAG] [--to-ref REF] [-o FILE]"
      echo "Generates a structured CHANGELOG.md from git history."
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# --- Determine range ---
if [[ -n "$FROM_TAG" ]]; then
  RANGE="${FROM_TAG}..${TO_REF}"
else
  # Auto-detect last tag
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo '')"
  if [[ -z "$LAST_TAG" ]]; then
    RANGE="${TO_REF}"  # all commits if no tags
  else
    RANGE="${LAST_TAG}..${TO_REF}"
  fi
fi

# --- Fetch commits ---
COMMITS=$(git log "$RANGE" --pretty=format:"%H|%s|%an|%ad" --date=short 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "# No changes detected" > "${OUTPUT_FILE:-/dev/stdout}"
  [[ -n "$OUTPUT_FILE" ]] && echo "Written to ${OUTPUT_FILE}" >&2
  exit 0
fi

# --- Categorize commits ---
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS='|' read -r hash subject author date; do
  subj_lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
  if   echo "$subj_lower" | grep -qE '^(add|feat|new|implement|create|introduce)'; then
    ADDED+=("- **${subject}** (${date}, ${author})")
  elif echo "$subj_lower" | grep -qE '^(fix|bug|patch|hotfix|resolve|close)'; then
    FIXED+=("- **${subject}** (${date}, ${author})")
  elif echo "$subj_lower" | grep -qE '^(change|update|modify|refactor|improve|tweak|adjust)'; then
    CHANGED+=("- **${subject}** (${date}, ${author})")
  elif echo "$subj_lower" | grep -qE '^(remove|delete|deprecate|drop)'; then
    REMOVED+=("- **${subject}** (${date}, ${author})")
  else
    OTHER+=("- **${subject}** (${date}, ${author})")
  fi
done <<< "$COMMITS"

# --- Get version info ---
TAG_NAME="${FROM_TAG:-unreleased}"
if [[ -z "$FROM_TAG" ]]; then
  TAG_NAME="$(git describe --tags --abbrev=0 2>/dev/null || echo 'unreleased')"
fi
TODAY=$(date +%Y-%m-%d)
COMMIT_COUNT=$(echo "$COMMITS" | wc -l)

# --- Build markdown ---
{
  echo "# Changelog"
  echo ""
  echo "## ${TAG_NAME} → ${TODAY} (${COMMIT_COUNT} commits)"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    printf '%s\n' "${ADDED[@]}"
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    printf '%s\n' "${FIXED[@]}"
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    printf '%s\n' "${CHANGED[@]}"
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    printf '%s\n' "${REMOVED[@]}"
    echo ""
  fi

  if [[ ${#OTHER[@]} -gt 0 ]]; then
    echo "### Other"
    printf '%s\n' "${OTHER[@]}"
    echo ""
  fi

  echo "---"
  echo "*Generated on ${TODAY} by changelog.sh*"
} > "${OUTPUT_FILE:-/dev/stdout}"

if [[ -n "$OUTPUT_FILE" ]]; then
  echo "✅ CHANGELOG written to ${OUTPUT_FILE} (${COMMIT_COUNT} commits)" >&2
fi
