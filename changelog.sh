#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

current_ref="$(git rev-parse --short HEAD)"
today="$(date +%Y-%m-%d)"

last_tag=""
if last_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range="${last_tag}..HEAD"
  range_label="since ${last_tag}"
else
  range="HEAD"
  range_label="from repository history"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_commit() {
  local subject="$1"
  local hash="$2"
  local line="- ${subject} (${hash})"
  local normalized
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*|remove\ *|delete\ *|drop\ *)
      removed+=("$line")
      ;;
    fix:*|fixed:*|bug:*|bugfix:*|repair:*|hotfix:*|fix\ *|resolve\ *|patch\ *)
      fixed+=("$line")
      ;;
    feat:*|feature:*|add:*|added:*|create:*|created:*|implement:*|implemented:*|feat\ *|add\ *|create\ *|implement\ *)
      added+=("$line")
      ;;
    *)
      changed+=("$line")
      ;;
  esac
}

while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue
  append_commit "$subject" "$hash"
done < <(git log "$range" --no-merges --pretty=format:'%h%x09%s')

write_section() {
  local title="$1"
  local array_name="$2"
  local entries=()

  case "$array_name" in
    added) entries=("${added[@]}") ;;
    fixed) entries=("${fixed[@]}") ;;
    changed) entries=("${changed[@]}") ;;
    removed) entries=("${removed[@]}") ;;
    *) echo "error: unknown changelog section ${array_name}" >&2; exit 1 ;;
  esac

  printf '\n### %s\n\n' "$title"
  if ((${#entries[@]} == 0)); then
    printf -- '- No changes.\n'
    return
  fi

  printf '%s\n' "${entries[@]}"
}

{
  printf '# Changelog\n\n'
  printf '## %s - %s\n\n' "$today" "$current_ref"
  printf '_Generated from git commits %s._\n' "$range_label"
  write_section "Added" added
  write_section "Fixed" fixed
  write_section "Changed" changed
  write_section "Removed" removed
  printf '\n'
} > "$OUTPUT_FILE"

echo "Wrote ${OUTPUT_FILE}"
