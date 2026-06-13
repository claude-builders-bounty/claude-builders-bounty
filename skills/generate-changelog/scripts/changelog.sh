#!/bin/bash
# =============================================================================
# changelog.sh ? Generate a structured CHANGELOG.md from git history
#
# Usage:
#   cd /path/to/your/repo
#   bash changelog.sh [--output CHANGELOG.md] [--tag v1.0.0]
#
# Categorizes commits into: Added / Fixed / Changed / Removed
# Works with conventional commits (feat:, fix:) and any format.
# =============================================================================

set -eo pipefail

OUTPUT="CHANGELOG.md"
TAG_OVERRIDE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --tag) TAG_OVERRIDE="$2"; shift 2 ;;
    *) break ;;
  esac
done

LAST_TAG="$TAG_OVERRIDE"
[ -z "$LAST_TAG" ] && LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"

if [ -z "$LAST_TAG" ]; then
  SINCE=""
  VERSION="v1.0.0"
else
  SINCE="${LAST_TAG}..HEAD"
  VERSION="$LAST_TAG"
fi

COMMITS=$(git log "$SINCE" --pretty=format:"%s|||%b" --no-merges 2>/dev/null || git log --pretty=format:"%s|||%b" --no-merges 2>/dev/null)

if [ -z "$COMMITS" ]; then
  echo "No commits found since last tag (or no tags exist)."
  exit 1
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS='|||' read -r title body; do
  [ -z "$title" ] && continue
  lc=$(echo "$title" | tr '[:upper:]' '[:lower:]')
  clean=$(echo "$title" | sed 's/^[^:]*:\s*//')
  case "$lc" in
    feat:*|feature:*|add:*|implement:*|introduce:*)
      ADDED+=("$clean") ;;
    fix:*|bugfix:*|patch:*|hotfix:*|correct:*)
      FIXED+=("$clean") ;;
    remove:*|delete:*|drop:*|deprecate:*|deprecated:*)
      REMOVED+=("$clean") ;;
    refactor:*|update:*|upgrade:*|bump:*|migrate:*|improve:*|change:*)
      CHANGED+=("$clean") ;;
    docs:*|chore:*|style:*|test:*|ci:*|build:*|perf:*|revert:*)
      CHANGED+=("$clean") ;;
    *)
      OTHER+=("$title") ;;
  esac
done < <(echo "$COMMITS")

cat > "$OUTPUT" << EOF
# Changelog

## ${VERSION} ($(date +%Y-%m-%d))

EOF

add_section() {
  local label="$1"; shift
  local items=("$@")
  [ ${#items[@]} -eq 0 ] && return
  echo "### $label" >> "$OUTPUT"
  for item in "${items[@]}"; do echo "- $item" >> "$OUTPUT"; done
  echo "" >> "$OUTPUT"
}

add_section "Added" "${ADDED[@]}"
add_section "Changed" "${CHANGED[@]}"
add_section "Fixed" "${FIXED[@]}"
add_section "Removed" "${REMOVED[@]}"
add_section "Other" "${OTHER[@]}"

echo "Done - CHANGELOG generated to ${OUTPUT}"
echo "  Added: ${#ADDED[@]}  Fixed: ${#FIXED[@]}  Changed: ${#CHANGED[@]}  Removed: ${#REMOVED[@]}"