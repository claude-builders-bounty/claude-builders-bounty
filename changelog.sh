#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--output CHANGELOG.md] [--since TAG]

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o) OUTPUT_FILE="$2"; shift 2 ;;
    --since|-s)  SINCE_TAG="$2"; shift 2 ;;
    --help|-h)   echo "Usage: bash changelog.sh [--output FILE] [--since TAG]"; exit 0 ;;
    *)           echo "Unknown: $1"; exit 1 ;;
  esac
done

# Determine the tag range
if [[ -z "$SINCE_TAG" ]]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$LAST_TAG" ]]; then
    SINCE_TAG="$LAST_TAG"
    RANGE="${SINCE_TAG}..HEAD"
  else
    RANGE="HEAD"
  fi
else
  RANGE="${SINCE_TAG}..HEAD"
fi

echo "📋 Generating CHANGELOG from $RANGE" >&2

# Categorize commits
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS= read -r line; do
  msg="${line#* }"  # strip the hash prefix
  case "$msg" in
    fea:*|feat:*|feature:*|add:*|added:*|implement:*)
      ADDED+=("$msg") ;;
    fix:*|bugfix:*|bug:*|hotfix:*|patch:*)
      FIXED+=("$msg") ;;
    chang:*|refactor:*|update:*|upgrade:*|deprecat:*|perf:*)
      CHANGED+=("$msg") ;;
    remov:*|delete:*|deprecat:*|dro:*)
      REMOVED+=("$msg") ;;
    *)
      # Categorize by keywords in the full message
      lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
      case "$lower" in
        *fix*|*bug*|*patch*|*hotfix*)       FIXED+=("$msg") ;;
        *add*|*feat*|*feature*|*implement*) ADDED+=("$msg") ;;
        *remov*|*delet*|*deprecat*|*drop*)  REMOVED+=("$msg") ;;
        *)                                   CHANGED+=("$msg") ;;
      esac ;;
  esac
done < <(git log "$RANGE" --oneline --no-decorate 2>/dev/null || echo "")

# Build the CHANGELOG
{
  echo "# Changelog"
  echo ""
  echo "> Generated from $(git log "$RANGE" --oneline 2>/dev/null | wc -l) commits"
  if [[ -n "$SINCE_TAG" ]]; then
    echo "> Since: $SINCE_TAG"
  fi
  echo ""

  today=$(date +%Y-%m-%d)
  echo "## [$today]"
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
} > "$OUTPUT_FILE"

echo "✅ Wrote $OUTPUT_FILE ($(wc -l < "$OUTPUT_FILE") lines)" >&2
