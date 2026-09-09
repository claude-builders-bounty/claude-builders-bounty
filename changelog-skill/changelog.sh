#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history since the last tag.
# Usage: bash changelog.sh [OUTPUT_FILE]
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
RANGE=""
SECTION_TITLE="Unreleased"
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  SECTION_TITLE="Unreleased (since ${LAST_TAG})"
fi

OUT="${1:-CHANGELOG.md}"

category() {
  local m
  m="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$m" in
    feat*|add*|new*|introduce*)           printf '%s' 'Added' ;;
    fix*|bug*|patch*|repair*|correct*)    printf '%s' 'Fixed' ;;
    revert*|remove*|delete*|drop*)        printf '%s' 'Removed' ;;
    *)                                    printf '%s' 'Changed' ;;
  esac
}

added=(); fixed=(); changed=(); removed=()
while IFS= read -r msg; do
  [ -z "$msg" ] && continue
  case "$(category "$msg")" in
    Added)   added+=("$msg") ;;
    Fixed)   fixed+=("$msg") ;;
    Removed) removed+=("$msg") ;;
    Changed) changed+=("$msg") ;;
  esac
done < <(git log $RANGE --no-merges --pretty=format:'%s' 2>/dev/null || true)

emit() {
  # emit "<Section>" <items...> — bash 3.2-safe empty-array expansion
  [ "$#" -lt 2 ] && return
  local title="$1"; shift
  printf '### %s\n' "$title"
  local it
  for it in "$@"; do printf -- '- %s\n' "$it"; done
  printf '\n'
}

TOTAL=$(( ${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]} ))
{
  printf '# Changelog\n\n'
  printf '## %s\n\n' "$SECTION_TITLE"
  emit 'Added'   ${added[@]+"${added[@]}"}
  emit 'Fixed'   ${fixed[@]+"${fixed[@]}"}
  emit 'Changed' ${changed[@]+"${changed[@]}"}
  emit 'Removed' ${removed[@]+"${removed[@]}"}
} > "$OUT"

if [ -n "$LAST_TAG" ]; then
  RANGE_LABEL="since ${LAST_TAG}"
else
  RANGE_LABEL="since the beginning of history (no tags found)"
fi
printf 'Wrote %s (%d commits %s)\n' "$OUT" "$TOTAL" "$RANGE_LABEL"
