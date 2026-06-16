#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository." >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  range_label="since ${last_tag}"
else
  range="HEAD"
  range_label="from repository history"
fi

declare -a added fixed changed removed

while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}${subject:-}" ]]; do
  [[ -n "${subject:-}" ]] || continue
  entry="- ${subject} (${hash})"
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feat\(*|add:*|add\ *|added\ *|implement\ *|create\ *)
      added+=("$entry")
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|repair\ *|resolve\ *)
      fixed+=("$entry")
      ;;
    remove:*|remove\ *|removed\ *|delete:*|delete\ *|drop\ *)
      removed+=("$entry")
      ;;
    *)
      changed+=("$entry")
      ;;
  esac
done < <(git log --no-merges --date-order --pretty=format:'%h%x09%s' "$range")

write_section() {
  local title="$1"
  shift
  local items=("$@")

  printf '### %s\n\n' "$title"
  if ((${#items[@]} == 0)); then
    printf -- '- No changes.\n\n'
    return
  fi

  printf '%s\n' "${items[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased (%s)\n\n' "$range_label"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$output_file"

echo "Wrote ${output_file}"
