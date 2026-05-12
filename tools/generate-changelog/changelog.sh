#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag=""
if latest_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range="HEAD"
  since_label="since repository start"
fi

mapfile -t commits < <(git log --reverse --pretty=format:'%s' "${range}")

added=()
fixed=()
changed=()
removed=()

for subject in "${commits[@]}"; do
  normalized="$(printf '%s' "${subject}" | tr '[:upper:]' '[:lower:]')"

  case "${normalized}" in
    feat:*|feat\(*|add:*|add\ *|added\ *|new\ *|create\ *|created\ *)
      added+=("${subject}")
      ;;
    fix:*|fix\(*|fixed\ *|bug:*|bugfix:*|patch:*|repair\ *)
      fixed+=("${subject}")
      ;;
    remove:*|removed\ *|delete:*|deleted\ *|drop:*|dropped\ *|deprecate:*|deprecated\ *)
      removed+=("${subject}")
      ;;
    *)
      changed+=("${subject}")
      ;;
  esac
done

write_section() {
  local title="$1"
  shift
  local items=("$@")

  {
    printf '### %s\n\n' "${title}"
    if ((${#items[@]} == 0)); then
      printf '%s\n\n' '- No matching commits.'
    else
      for item in "${items[@]}"; do
        printf -- '- %s\n' "${item}"
      done
      printf '\n'
    fi
  } >>"${output_file}"
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased\n\n'
  printf '_Generated from git commits %s._\n\n' "${since_label}"
} >"${output_file}"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

printf 'Wrote %s from %d commit(s) %s.\n' "${output_file}" "${#commits[@]}" "${since_label}"
