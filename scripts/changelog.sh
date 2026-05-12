#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must run inside a git repository" >&2
  exit 1
fi

last_tag=""
if last_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${last_tag}..HEAD"
  since_label="since ${last_tag}"
else
  range="HEAD"
  since_label="from project start"
fi

mapfile -t commits < <(git log --pretty=format:'%s' "$range")

added=()
fixed=()
changed=()
removed=()

categorize() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    fix:*|fixed:*|bugfix:*|*" fix "*|*" bug "*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|*" remove "*|*" delete "*) echo "Removed" ;;
    change:*|changed:*|refactor:*|update:*|updated:*|*" change "*|*" refactor "*) echo "Changed" ;;
    add:*|added:*|feat:*|feature:*|create:*|created:*|*" add "*|*" feature "*) echo "Added" ;;
    *) echo "Changed" ;;
  esac
}

for subject in "${commits[@]}"; do
  [ -n "$subject" ] || continue
  case "$(categorize "$subject")" in
    Added) added+=("$subject") ;;
    Fixed) fixed+=("$subject") ;;
    Changed) changed+=("$subject") ;;
    Removed) removed+=("$subject") ;;
  esac
done

write_section() {
  local title="$1"
  local array_name="$2"
  local -n items_ref="$array_name"
  printf '\n### %s\n' "$title"
  if [ "${#items_ref[@]}" -eq 0 ]; then
    printf -- '- None\n'
    return
  fi
  local item
  for item in "${items_ref[@]}"; do
    printf -- '- %s\n' "$item"
  done
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased (%s)\n' "$since_label"
  write_section "Added" added
  write_section "Fixed" fixed
  write_section "Changed" changed
  write_section "Removed" removed
} > "$OUTPUT_FILE"

printf 'Wrote %s using commits %s\n' "$OUTPUT_FILE" "$since_label"
