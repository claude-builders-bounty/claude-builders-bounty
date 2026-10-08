#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf '%s\n' 'Error: run this command inside a Git repository.' >&2
  exit 2
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="$LAST_TAG..HEAD"
  COMMIT_LOG="$(git log --no-merges "$RANGE" --pretty=format:'%s')"
  BASELINE="$LAST_TAG"
else
  RANGE="HEAD"
  COMMIT_LOG="$(git log --no-merges HEAD --pretty=format:'%s')"
  BASELINE="repository start (no reachable tag)"
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

RE_FEAT='^feat(\([^)]*\))?!?:[[:space:]]*'
RE_FIX='^fix(\([^)]*\))?!?:[[:space:]]*'
RE_REMOVE='^(remove|delete|drop)(\([^)]*\))?!?:[[:space:]]*'
RE_ADDED_WORD='^(add|create|implement|introduce)[[:space:]]'
RE_FIXED_WORD='^(fix|repair|resolve)[[:space:]]'
RE_REMOVED_WORD='^(remove|delete|drop)[[:space:]]'
shopt -s nocasematch

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  if [[ "$line" =~ $RE_FEAT || "$line" =~ $RE_ADDED_WORD ]]; then
    ADDED+=("$line")
  elif [[ "$line" =~ $RE_FIX || "$line" =~ $RE_FIXED_WORD ]]; then
    FIXED+=("$line")
  elif [[ "$line" =~ $RE_REMOVE || "$line" =~ $RE_REMOVED_WORD ]]; then
    REMOVED+=("$line")
  else
    CHANGED+=("$line")
  fi
done <<< "$COMMIT_LOG"

{
  printf '## [Unreleased]\n\n'
  printf '<!-- Generated from commits after: %s -->\n\n' "$BASELINE"

  if ((${#ADDED[@]})); then
    printf '### Added\n'
    printf -- '- %s\n' "${ADDED[@]}"
    printf '\n'
  fi
  if ((${#FIXED[@]})); then
    printf '### Fixed\n'
    printf -- '- %s\n' "${FIXED[@]}"
    printf '\n'
  fi
  if ((${#CHANGED[@]})); then
    printf '### Changed\n'
    printf -- '- %s\n' "${CHANGED[@]}"
    printf '\n'
  fi
  if ((${#REMOVED[@]})); then
    printf '### Removed\n'
    printf -- '- %s\n' "${REMOVED[@]}"
    printf '\n'
  fi

  if ((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} == 0)); then
    printf 'No changes since %s.\n' "$BASELINE"
  fi
} > CHANGELOG.md

printf 'Generated CHANGELOG.md from %s.\n' "$BASELINE"
