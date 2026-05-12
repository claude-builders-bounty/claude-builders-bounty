#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag=""
if latest_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  commit_range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  commit_range="HEAD"
  range_label="from the full repository history"
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
today="$(date +%Y-%m-%d)"
version_label="Unreleased"

added=()
fixed=()
changed=()
removed=()

categorize_commit() {
  local subject="$1"
  local lowered
  lowered="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lowered" in
    feat:*|feat\(*|feature:*|feature\(*|add:*|add\ *|added\ *|create:*|create\ *|implement:*|implement\ *|introduce:*|introduce\ *)
      echo "Added"
      ;;
    fix:*|fix\(*|fixed\ *|bugfix:*|hotfix:*|repair:*|resolve:*|resolve\ *|patch:*)
      echo "Fixed"
      ;;
    remove:*|remove\ *|removed\ *|delete:*|delete\ *|deleted\ *|drop:*|drop\ *|deprecate:*|deprecate\ *)
      echo "Removed"
      ;;
    *)
      echo "Changed"
      ;;
  esac
}

clean_subject() {
  local subject="$1"

  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"

  if [ -z "$subject" ]; then
    subject="Update project files"
  fi

  first_char="$(printf '%s' "$subject" | cut -c 1 | tr '[:lower:]' '[:upper:]')"
  rest="$(printf '%s' "$subject" | cut -c 2-)"
  printf '%s%s' "$first_char" "$rest"
}

append_item() {
  local category="$1"
  local item="$2"

  case "$category" in
    Added) added+=("$item") ;;
    Fixed) fixed+=("$item") ;;
    Removed) removed+=("$item") ;;
    *) changed+=("$item") ;;
  esac
}

while IFS=$'\t' read -r short_hash subject; do
  [ -n "${short_hash:-}" ] || continue

  category="$(categorize_commit "$subject")"
  cleaned="$(clean_subject "$subject")"
  append_item "$category" "${cleaned} (${short_hash})"
done < <(git log --no-merges --pretty=format:'%h%x09%s' "$commit_range")

write_section() {
  local title="$1"
  local empty_label="$2"
  shift
  shift
  local items=("$@")

  printf '### %s\n\n' "$title"
  if [ "${#items[@]}" -eq 0 ]; then
    printf -- '- No %s changes.\n\n' "$empty_label"
    return
  fi

  local item
  for item in "${items[@]}"; do
    printf -- '- %s\n' "$item"
  done
  printf '\n'
}

set +u
{
  printf '# Changelog\n\n'
  printf 'All notable changes to `%s` are documented in this file.\n\n' "$repo_name"
  printf '## %s - %s\n\n' "$version_label" "$today"
  printf '_Generated from git commits %s._\n\n' "$range_label"
  write_section "Added" "added" "${added[@]}"
  write_section "Fixed" "fixed" "${fixed[@]}"
  write_section "Changed" "changed" "${changed[@]}"
  write_section "Removed" "removed" "${removed[@]}"
} > "$output_file"
set -u

echo "Wrote ${output_file}"
