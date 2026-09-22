#!/usr/bin/env bash
#
# changelog.sh — generate a structured CHANGELOG.md from git history.
#
# Collects commits since the most recent git tag (or the whole history if
# there are no tags) and categorises them into Added / Changed / Fixed /
# Removed using Conventional-Commit prefixes first, then keyword heuristics.
#
# Usage:
#   bash changelog.sh                 # print to stdout
#   bash changelog.sh -o CHANGELOG.md # write/prepend to a file
#   bash changelog.sh --since v1.2.0  # explicit starting ref
#   bash changelog.sh --version 1.3.0 # header version (default: next tag guess)
#
set -euo pipefail

OUT=""
SINCE=""
VERSION=""

while [ $# -gt 0 ]; do
  case "$1" in
    -o|--output) OUT="${2:-}"; shift 2 ;;
    --since)     SINCE="${2:-}"; shift 2 ;;
    --version)   VERSION="${2:-}"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [-o CHANGELOG.md] [--since <ref>] [--version <x.y.z>]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

# Must be inside a git repo.
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

# Determine the starting point: explicit --since, else the latest tag.
if [ -z "$SINCE" ]; then
  SINCE="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [ -n "$SINCE" ]; then
  RANGE="${SINCE}..HEAD"
  PREV_DESC="since ${SINCE}"
else
  RANGE="HEAD"                      # no tags: whole history
  PREV_DESC="full history"
fi

# Header version: explicit, else "Unreleased".
[ -z "$VERSION" ] && VERSION="Unreleased"
DATE="$(date -u +%Y-%m-%d)"

# Collect commit subjects for the range (subject only, one per line).
mapfile -t COMMITS < <(git log "$RANGE" --no-merges --pretty=format:'%s' 2>/dev/null || true)

added=(); changed=(); fixed=(); removed=()

classify() {
  # Return category for a commit subject.
  local s="$1" low
  low="$(printf '%s' "$s" | tr '[:upper:]' '[:lower:]')"
  case "$low" in
    feat:*|feat\(*|add:*|added:*)                 echo added ;;
    fix:*|fix\(*|bugfix:*|hotfix:*)               echo fixed ;;
    remove:*|removed:*|revert:*|delete:*|"revert "*) echo removed ;;
    refactor:*|refactor\(*|change:*|changed:*|perf:*|perf\(*|chore:*|docs:*|style:*|update:*|updated:*) echo changed ;;
    *)
      # keyword heuristics for non-conventional commits
      case "$low" in
        add\ *|adds\ *|added\ *|introduce*|implement*|new\ *)  echo added ;;
        fix*|resolve*|repair*|correct*|patch*)                echo fixed ;;
        remove*|delete*|drop\ *|deprecate*)                   echo removed ;;
        *)                                                     echo changed ;;
      esac ;;
  esac
}

# Strip a leading conventional-commit prefix for cleaner bullets.
clean_subject() {
  printf '%s' "$1" | sed -E 's/^([a-zA-Z]+)(\([^)]*\))?!?:[[:space:]]*//'
}

for c in "${COMMITS[@]:-}"; do
  [ -z "$c" ] && continue
  cat="$(classify "$c")"
  entry="$(clean_subject "$c")"
  # Capitalise first letter.
  entry="$(printf '%s' "$entry" | sed -E 's/^(.)/\U\1/')"
  case "$cat" in
    added)   added+=("$entry") ;;
    fixed)   fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    *)       changed+=("$entry") ;;
  esac
done

emit_section() {
  local title="$1"; shift
  local -a items=("$@")
  [ "${#items[@]}" -eq 0 ] && return 0
  printf '### %s\n\n' "$title"
  local i
  for i in "${items[@]}"; do printf -- '- %s\n' "$i"; done
  printf '\n'
}

# Build the new changelog block.
BLOCK="$(
  printf '## [%s] - %s\n\n' "$VERSION" "$DATE"
  if [ $(( ${#added[@]} + ${#changed[@]} + ${#fixed[@]} + ${#removed[@]} )) -eq 0 ]; then
    printf -- '- No changes recorded (%s).\n\n' "$PREV_DESC"
  else
    emit_section "Added"   "${added[@]:-}"
    emit_section "Changed" "${changed[@]:-}"
    emit_section "Fixed"   "${fixed[@]:-}"
    emit_section "Removed" "${removed[@]:-}"
  fi
)"

HEADER="# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/), categories
derived from git history ($PREV_DESC).
"

if [ -n "$OUT" ]; then
  if [ -f "$OUT" ] && grep -q '^# Changelog' "$OUT"; then
    # Prepend the new block just after the header's blank line.
    tmp="$(mktemp)"
    { printf '%s\n' "$HEADER"; printf '%s\n' "$BLOCK";
      # keep existing entries (everything after the first '## ' onward)
      awk 'f{print} /^## /{if(!f){f=1; print}}' "$OUT"; } > "$tmp"
    mv "$tmp" "$OUT"
  else
    { printf '%s\n' "$HEADER"; printf '%s\n' "$BLOCK"; } > "$OUT"
  fi
  echo "Wrote changelog to $OUT"
else
  printf '%s\n' "$HEADER"
  printf '%s\n' "$BLOCK"
fi
