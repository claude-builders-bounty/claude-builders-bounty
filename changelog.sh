#!/usr/bin/env bash

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_NAME="$(basename "$(git rev-parse --show-toplevel)")"
TODAY="$(date +%Y-%m-%d)"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  RANGE_LABEL="from repository history"
fi

COMMITS="$(git log "$RANGE" --pretty=format:'%H%x1f%s%x1f%an%x1f%ad' --date=short --no-merges)"

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

append_commit() {
  local category="$1"
  local hash="$2"
  local subject="$3"
  local author="$4"
  local date="$5"
  local short_hash

  short_hash="$(git rev-parse --short "$hash")"
  local entry="- ${subject} (${short_hash}, ${date}, ${author})"

  case "$category" in
    Added) ADDED+=("$entry") ;;
    Fixed) FIXED+=("$entry") ;;
    Changed) CHANGED+=("$entry") ;;
    Removed) REMOVED+=("$entry") ;;
  esac
}

categorize_subject() {
  local subject_lower
  subject_lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject_lower" in
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*|*' remove '*|*' delete '*|*' drop '*)
      printf 'Removed'
      ;;
    fix:*|fixed:*|bugfix:*|bug:*|hotfix:*|patch:*|*' fix '*|*' bug '*|*' error '*|*' crash '*)
      printf 'Fixed'
      ;;
    feat:*|feature:*|add:*|added:*|new:*|create:*|created:*|implement:*|implemented:*|*' add '*|*' introduce '*)
      printf 'Added'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

if [[ -n "$COMMITS" ]]; then
  while IFS=$'\x1f' read -r hash subject author date; do
    category="$(categorize_subject "$subject")"
    append_commit "$category" "$hash" "$subject" "$author" "$date"
  done <<< "$COMMITS"
fi

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  {
    printf '### %s\n\n' "$title"
    if (( ${#entries[@]} == 0 )); then
      printf -- '- No changes.\n'
    else
      printf '%s\n' "${entries[@]}"
    fi
  } >> "$OUTPUT_FILE"
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes for `%s` are listed here.\n\n' "$REPO_NAME"
  printf '## %s (%s)\n\n' "$TODAY" "$RANGE_LABEL"
} > "$OUTPUT_FILE"

write_section "Added" "${ADDED[@]}"
printf '\n\n' >> "$OUTPUT_FILE"
write_section "Fixed" "${FIXED[@]}"
printf '\n\n' >> "$OUTPUT_FILE"
write_section "Changed" "${CHANGED[@]}"
printf '\n\n' >> "$OUTPUT_FILE"
write_section "Removed" "${REMOVED[@]}"

echo "Generated ${OUTPUT_FILE} ${RANGE_LABEL}."
