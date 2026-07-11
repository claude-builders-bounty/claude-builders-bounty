#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   ./changelog.sh                    # writes CHANGELOG.md in current directory
#   ./changelog.sh -o RELEASE.md      # custom output filename
#   ./changelog.sh -t v1.0.0          # start from a specific tag
#
# Auto-categorizes commits into: Added / Fixed / Changed / Removed

set -euo pipefail

OUTPUT="CHANGELOG.md"
START_TAG=""

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      OUTPUT="$2"; shift 2 ;;
    -t|--tag)
      START_TAG="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [-o OUTPUT] [-t TAG]"
      echo "  -o, --output   Output file (default: CHANGELOG.md)"
      echo "  -t, --tag      Start from this tag (default: latest tag)"
      exit 0 ;;
    *)
      echo "Unknown option: $1"; exit 1 ;;
  esac
done

# --- Determine starting point ---
if [[ -z "$START_TAG" ]]; then
  START_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -n "$START_TAG" ]]; then
  RANGE="${START_TAG}..HEAD"
  echo "→ Collecting commits since tag: $START_TAG"
else
  RANGE="HEAD"
  echo "→ No tags found — collecting all commits"
fi

# --- Fetch commits ---
COMMITS=$(git log "$RANGE" --no-merges --pretty=format:"%s" 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "⚠️  No commits found in range: $RANGE"
  COMMITS=""
fi

# --- Categorization ---
declare -a ADDED FIXED CHANGED REMOVED

while IFS= read -r line; do
  [[ -z "$line" ]] && continue

  # Normalize: trim whitespace, lowercase for matching
  lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')

  if   [[ "$lower" =~ ^(add|added|feat|feature|new|introduce) ]]; then
    ADDED+=("$line")
  elif [[ "$lower" =~ ^(fix|fixed|bug|patch|resolve|hotfix) ]]; then
    FIXED+=("$line")
  elif [[ "$lower" =~ ^(remove|removed|drop|delete|deprecate) ]]; then
    REMOVED+=("$line")
  else
    CHANGED+=("$line")
  fi
done <<< "$COMMITS"

# --- Generate CHANGELOG ---
{
  echo "# Changelog"
  echo ""
  echo "## $(git describe --tags --abbrev=0 2>/dev/null || echo 'Unreleased') — $(date +%Y-%m-%d)"
  echo ""

  section() {
    local title="$1"
    shift
    local -a items=("$@")
    if [[ ${#items[@]} -gt 0 ]]; then
      echo "### $title"
      echo ""
      for item in "${items[@]}"; do
        echo "- ${item}"
      done
      echo ""
    fi
  }

  section "Added"   "${ADDED[@]}"
  section "Fixed"   "${FIXED[@]}"
  section "Changed" "${CHANGED[@]}"
  section "Removed" "${REMOVED[@]}"

  # --- Stats footer ---
  total=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]}))
  echo "---"
  echo ""
  echo "*Generated on $(date -u +"%Y-%m-%dT%H:%M:%SZ") • ${total} commits since ${START_TAG:-initial commit}*"
} > "$OUTPUT"

echo "✅ CHANGELOG written to: $OUTPUT"
echo "   Added:   ${#ADDED[@]}"
echo "   Fixed:   ${#FIXED[@]}"
echo "   Changed: ${#CHANGED[@]}"
echo "   Removed: ${#REMOVED[@]}"