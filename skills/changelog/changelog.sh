#!/usr/bin/env bash
set -o pipefail

REPO="$(pwd)"
SINCE_TAG=""
OUTPUT="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --tag) SINCE_TAG="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --help|-h) echo "Usage: $0 [--repo path] [--tag v1.0.0] [--output CHANGELOG.md]"; exit 0 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

cd "$REPO" 2>/dev/null || { echo "Error: cannot access $REPO"; exit 1; }

if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD 2>/dev/null)
fi
SINCE_REF=$(git rev-parse --short "$SINCE_TAG" 2>/dev/null || echo "$SINCE_TAG")

# Use %x09 (tab) as delimiter (won't appear in commit messages)
COMMITS=$(git log "$SINCE_REF"..HEAD --format="%H%x09%an%x09%s" --no-merges 2>/dev/null)
if [[ -z "$COMMITS" ]]; then
  COMMITS=$(git log --format="%H%x09%an%x09%s" -30 --no-merges 2>/dev/null)
  [[ -n "$COMMITS" ]] && echo "No new commits since $SINCE_REF, showing last 30" >&2
fi
[[ -z "$COMMITS" ]] && { echo "No commits found"; exit 0; }

CAT_ADDED=(); CAT_FIXED=(); CAT_CHANGED=(); CAT_REMOVED=(); CAT_OTHER=()

while IFS="$(printf '\t')" read -r hash author msg; do
  [[ -z "$hash" ]] && continue
  msg_lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
  entry="+ **${msg}** — ${author} (${hash:0:7})"

  if echo "$msg_lower" | grep -qE '^(fix|bug|hotfix)'; then
    CAT_FIXED+=("$entry")
  elif echo "$msg_lower" | grep -qE '^(add|new|feat|introduce|create)'; then
    CAT_ADDED+=("$entry")
  elif echo "$msg_lower" | grep -qE '^(remove|delete|drop)'; then
    CAT_REMOVED+=("$entry")
  elif echo "$msg_lower" | grep -qE '^(change|refactor|update|improve|migrate)'; then
    CAT_CHANGED+=("$entry")
  else
    CAT_OTHER+=("$entry")
  fi
done <<< "$COMMITS"

DATE=$(date +%Y-%m-%d)
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.1.0")

{
  echo "# Changelog"
  echo ""
  echo "## [${VERSION}] - ${DATE}"
  echo ""
  [[ ${#CAT_ADDED[@]} -gt 0 ]] && { echo "### Added"; printf '  %s\n' "${CAT_ADDED[@]}"; echo ""; }
  [[ ${#CAT_FIXED[@]} -gt 0 ]] && { echo "### Fixed"; printf '  %s\n' "${CAT_FIXED[@]}"; echo ""; }
  [[ ${#CAT_CHANGED[@]} -gt 0 ]] && { echo "### Changed"; printf '  %s\n' "${CAT_CHANGED[@]}"; echo ""; }
  [[ ${#CAT_REMOVED[@]} -gt 0 ]] && { echo "### Removed"; printf '  %s\n' "${CAT_REMOVED[@]}"; echo ""; }
  [[ ${#CAT_OTHER[@]} -gt 0 ]] && { echo "### Other"; printf '  %s\n' "${CAT_OTHER[@]}"; echo ""; }
} > "$OUTPUT"

echo "CHANGELOG generated at ${OUTPUT} ($(wc -l < "${OUTPUT}") lines)"
