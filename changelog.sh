#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must run inside a Git repository" >&2
  exit 1
fi

git fetch --tags --quiet 2>/dev/null || true

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range="HEAD"
  since_label="from repository history"
fi

mapfile -t commits < <(git log --no-merges --pretty=format:'%s%x1f%h' "$range")

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_entry() {
  local category="$1"
  local subject="$2"
  local sha="$3"
  local entry="- ${subject} (${sha})"

  case "$category" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Changed) changed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
  esac
}

category_for_subject() {
  local subject_lc
  subject_lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject_lc" in
    feat:*|feat\(*|add:*|added:*|create:*|implement:*) echo "Added" ;;
    fix:*|fix\(*|bugfix:*|repair:*|patch:*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|drop:*|deprecate:*) echo "Removed" ;;
    change:*|changed:*|refactor:*|perf:*|docs:*|test:*|chore:*|build:*|ci:*|style:*|rework:*|update:*) echo "Changed" ;;
    *) echo "Changed" ;;
  esac
}

for commit in "${commits[@]}"; do
  [[ -z "$commit" ]] && continue
  subject="${commit%%$'\x1f'*}"
  sha="${commit##*$'\x1f'}"
  append_entry "$(category_for_subject "$subject")" "$subject" "$sha"
done

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title"
  if ((${#entries[@]} == 0)); then
    printf -- '- No changes.\n\n'
    return
  fi
  printf '%s\n' "${entries[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$since_label"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} >"$output_file"

echo "Wrote ${output_file} (${#commits[@]} commits, ${since_label})."
