#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
VERSION_LABEL="${2:-Unreleased}"
TODAY="$(date +%Y-%m-%d)"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: current directory is not a git repository." >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_NOTE="Commits since \`${LAST_TAG}\`"
else
  RANGE="HEAD"
  RANGE_NOTE="Initial history"
fi

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

while IFS='|' read -r short_hash subject; do
  [[ -z "$short_hash" ]] && continue
  if [[ "$subject" =~ ^Merge[[:space:]] ]] || [[ "$subject" =~ ^chore\(release\): ]]; then
    continue
  fi

  entry="- ${subject} (\`${short_hash}\`)"
  lower_subj="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower_subj" =~ ^feat(\([^)]+\))?!?: ]] || [[ "$lower_subj" =~ ^(add|added|implement|create|introduce)[[:space:]] ]]; then
    ADDED+=("$entry")
  elif [[ "$lower_subj" =~ ^fix(\([^)]+\))?!?: ]] || [[ "$lower_subj" =~ ^(fix|fixed|bug|patch|resolve|hotfix)[[:space:]] ]]; then
    FIXED+=("$entry")
  elif [[ "$lower_subj" =~ ^(remove|removed|delete|deleted|drop|deprecate|revert)[[:space:]:] ]]; then
    REMOVED+=("$entry")
  else
    CHANGED+=("$entry")
  fi
done < <(git log "$RANGE" --pretty=format:'%h|%s')

total=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))

{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project will be documented in this file.\n\n'
  printf '## [%s] - %s\n\n' "$VERSION_LABEL" "$TODAY"
  printf '_%s_\n\n' "$RANGE_NOTE"

  if (( total == 0 )); then
    printf '_No notable commits in this range._\n'
  else
    if (( ${#ADDED[@]} > 0 )); then
      printf '### Added\n'
      printf '%s\n' "${ADDED[@]}"
      printf '\n'
    fi
    if (( ${#FIXED[@]} > 0 )); then
      printf '### Fixed\n'
      printf '%s\n' "${FIXED[@]}"
      printf '\n'
    fi
    if (( ${#CHANGED[@]} > 0 )); then
      printf '### Changed\n'
      printf '%s\n' "${CHANGED[@]}"
      printf '\n'
    fi
    if (( ${#REMOVED[@]} > 0 )); then
      printf '### Removed\n'
      printf '%s\n' "${REMOVED[@]}"
      printf '\n'
    fi
  fi
} > "$OUTPUT_FILE"

printf 'Generated %s (%s: %d Added, %d Fixed, %d Changed, %d Removed)\n' \
  "$OUTPUT_FILE" "$RANGE_NOTE" "${#ADDED[@]}" "${#FIXED[@]}" "${#CHANGED[@]}" "${#REMOVED[@]}"
