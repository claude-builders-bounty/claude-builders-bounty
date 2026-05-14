#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
else
  range="HEAD"
fi

commit_lines="$(git log "$range" --pretty=format:'%s' --no-merges)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

clean_subject() {
  local subject="$1"
  subject="$(printf '%s\n' "$subject" | sed -E 's/^[[:alnum:]_-]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="${subject#- }"
  printf '%s\n' "$subject"
}

append_item() {
  local category="$1"
  local subject="$2"
  local cleaned

  cleaned="$(clean_subject "$subject")"
  case "$category" in
    added) added+=("$cleaned") ;;
    fixed) fixed+=("$cleaned") ;;
    changed) changed+=("$cleaned") ;;
    removed) removed+=("$cleaned") ;;
  esac
}

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue

  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$normalized" in
    feat:*|feat\(*|feature:*|feature\(*|add:*|added:*|add\ *) append_item added "$subject" ;;
    fix:*|fix\(*|fixed:*|bugfix:*|bugfix\(*|bug:*|repair:*|fix\ *) append_item fixed "$subject" ;;
    remove:*|remove\(*|removed:*|delete:*|delete\(*|deleted:*|drop:*|drop\(*|dropped:*|remove\ *) append_item removed "$subject" ;;
    *) append_item changed "$subject" ;;
  esac
done <<< "$commit_lines"

write_section() {
  local title="$1"
  shift
  local items=("$@")

  [[ "${#items[@]}" -eq 0 ]] && return

  printf '### %s\n\n' "$title"
  for item in "${items[@]}"; do
    printf -- '- %s\n' "$item"
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  if [[ -n "$latest_tag" ]]; then
    printf 'Changes since `%s`.\n\n' "$latest_tag"
  else
    printf 'Changes from all commits.\n\n'
  fi
  printf '## Unreleased\n\n'

  if [[ -z "$commit_lines" ]]; then
    printf 'No changes found.\n'
  else
    write_section "Added" "${added[@]}"
    write_section "Fixed" "${fixed[@]}"
    write_section "Changed" "${changed[@]}"
    write_section "Removed" "${removed[@]}"
  fi
} > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE"
