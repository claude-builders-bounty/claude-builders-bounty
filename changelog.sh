#!/usr/bin/env bash
set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag|-t) SINCE_TAG="$2"; shift 2 ;;
    --output|-o) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

SINCE_REF="${SINCE_TAG:+$SINCE_TAG..}HEAD"
echo "Generating changelog since ${SINCE_TAG:-beginning}..."

ADDED=(); FIXED=(); CHANGED=(); REMOVED=(); OTHER=()

while IFS= read -r commit; do
  hash=$(echo "$commit" | cut -d' ' -f1)
  msg=$(echo "$commit" | cut -d' ' -f2-)
  case "$msg" in
    feat:*|add:*|implement:*|Feat:*|Add:*|Implement:*) ADDED+=("$hash|$msg") ;;
    fix:*|bug:*|patch:*|Fix:*|Bug:*|Patch:*) FIXED+=("$hash|$msg") ;;
    refactor:*|update:*|improve:*|Refactor:*|Update:*|Improve:*) CHANGED+=("$hash|$msg") ;;
    remove:*|deprecate:*|delete:*|Remove:*|Deprecate:*|Delete:*) REMOVED+=("$hash|$msg") ;;
    *) OTHER+=("$hash|$msg") ;;
  esac
done < <(git log "${SINCE_REF}" --oneline --no-decorate 2>/dev/null)

{
  echo "# Changelog"
  echo ""
  echo "> Generated on $(date +%Y-%m-%d)"
  [[ -n "$SINCE_TAG" ]] && echo "> Since: $SINCE_TAG"
  echo ""
  write_section() {
    local title="$1" icon="$2"; shift 2; local items=("$@")
    if [[ ${#items[@]} -gt 0 ]]; then
      echo "## $icon $title"; echo ""
      for item in "${items[@]}"; do
        local h="${item%%|*}"; local m="${item#*|}"
        echo "- $m (\`${h:0:7}\`)"
      done; echo ""
    fi
  }
  write_section "Added" "🚀" "${ADDED[@]}"
  write_section "Fixed" "🐛" "${FIXED[@]}"
  write_section "Changed" "🔄" "${CHANGED[@]}"
  write_section "Removed" "🗑️" "${REMOVED[@]}"
  write_section "Other" "📋" "${OTHER[@]}"
} > "$OUTPUT"

echo "Written to $OUTPUT"