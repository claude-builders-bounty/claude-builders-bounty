#!/usr/bin/env bash
#
# changelog.sh — Generate a categorized CHANGELOG.md from git history.
#
# Usage:
#   ./changelog.sh [--since <ref>] [--out <file>] [--tag-pattern <glob>]
#
# Fetches commits since the last git tag (or --since ref) and groups them into
# Added / Fixed / Changed / Removed using conventional-commit prefixes.
# Falls back gracefully when there are no tags yet.
#
set -euo pipefail

OUT="CHANGELOG.md"
SINCE=""
TAG_PATTERN="*"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --out)   OUT="$2";   shift 2 ;;
    --tag-pattern) TAG_PATTERN="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# Determine the start ref: explicit --since, else the most recent tag.
if [[ -z "$SINCE" ]]; then
  LATEST_TAG=$(git describe --tags --abbrev=0 --match "$TAG_PATTERN" 2>/dev/null || true)
  if [[ -n "$LATEST_TAG" ]]; then
    SINCE="$LATEST_TAG"
    RANGE="${SINCE}..HEAD"
    SECTION_TITLE="Changes since ${SINCE}"
  else
    SINCE="$(git rev-list --max-parents=0 HEAD 2>/dev/null | head -1 || true)"
    if [[ -n "$SINCE" ]]; then
      RANGE="${SINCE}..HEAD"
      SECTION_TITLE="Changelog (full history)"
    else
      # Shallow clone / no root commit reachable — use all of HEAD.
      RANGE="HEAD"
      SECTION_TITLE="Changelog (full history)"
    fi
  fi
else
  RANGE="${SINCE}..HEAD"
  SECTION_TITLE="Changes since ${SINCE}"
fi

# Collect commits (skip the boundary commit when using a tag).
mapfile -t COMMITS < <(git log "${RANGE}" --pretty=format:"%s" --no-merges)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  echo "No commits found in range ${RANGE}." >&2
  exit 0
fi

# Categorize by conventional-commit prefix (case-insensitive).
ADDED=(); FIXED=(); CHANGED=(); REMOVED=(); OTHER=()
for c in "${COMMITS[@]}"; do
  lower="$(printf '%s' "$c" | tr '[:upper:]' '[:lower:]')"
  if   [[ "$lower" =~ ^(feat|add|feature)(:|\(| ) ]]; then ADDED+=("$c")
  elif [[ "$lower" =~ ^(fix|bugfix)(:|\(| ) ]];        then FIXED+=("$c")
  elif [[ "$lower" =~ ^(change|refactor|perf|improve)(:|\(| ) ]]; then CHANGED+=("$c")
  elif [[ "$lower" =~ ^(remove|rm|delete)(:|\(| ) ]];  then REMOVED+=("$c")
  else OTHER+=("$c")
  fi
done

DATE=$(date +%Y-%m-%d)

emit() {
  local label="$1"; shift
  local -a items=("$@")
  (( ${#items[@]} == 0 )) && return
  echo "### $label"
  echo
  printf -- '- %s\n' "${items[@]}"
  echo
}

{
  echo "# Changelog"
  echo
  echo "All notable changes to this project are documented here."
  echo
  echo "## [$DATE] — $SECTION_TITLE"
  echo
  emit "Added"   "${ADDED[@]}"
  emit "Fixed"   "${FIXED[@]}"
  emit "Changed" "${CHANGED[@]}"
  emit "Removed" "${REMOVED[@]}"
  (( ${#OTHER[@]} > 0 )) && emit "Other" "${OTHER[@]}"
} > "$OUT"

echo "Wrote $OUT ($(grep -c '^- ' "$OUT" 2>/dev/null || true) entries) from range $RANGE"
