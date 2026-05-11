#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  heading="Unreleased changes since ${latest_tag}"
else
  range="HEAD"
  heading="Project changelog"
fi

declare -a added fixed changed removed

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower_subject" in
    feat:*|feat\(*|add:*|added:*|create:*|new:*)
      added+=("$subject")
      ;;
    fix:*|fix\(*|bugfix:*|hotfix:*|repair:*)
      fixed+=("$subject")
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*)
      removed+=("$subject")
      ;;
    *)
      changed+=("$subject")
      ;;
  esac
done < <(git log --no-merges --pretty=format:%s "$range")

write_section() {
  local title="$1"
  shift
  local items=("$@")

  printf '### %s\n\n' "$title"
  if (( ${#items[@]} == 0 )); then
    printf -- '- No changes.\n\n'
    return
  fi

  for item in "${items[@]}"; do
    printf -- '- %s\n' "$item"
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## %s\n\n' "$heading"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$output_file"

echo "Wrote ${output_file}"
