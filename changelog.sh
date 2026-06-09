#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

last_tag=""
if last_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  commit_range="${last_tag}..HEAD"
  since_label="since ${last_tag}"
else
  commit_range="HEAD"
  since_label="for all commits"
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
generated_at="$(date -u +%Y-%m-%d)"

mapfile -t commits < <(git log --no-merges --pretty=format:'%s%x09%h' "$commit_range")

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

clean_subject() {
  local subject="$1"
  subject="${subject#[[:space:]]}"
  subject="${subject%[[:space:]]}"
  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  printf '%s' "$subject"
}

append_item() {
  local category="$1"
  local subject="$2"
  local sha="$3"
  local item="$(clean_subject "$subject") (${sha})"

  case "$category" in
    added) added+=("$item") ;;
    fixed) fixed+=("$item") ;;
    changed) changed+=("$item") ;;
    removed) removed+=("$item") ;;
  esac
}

categorize() {
  local subject_lower
  subject_lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject_lower" in
    feat:*|feat\(*|add:*|add\(*|added:*|new:*|*" add "*|add\ *) printf 'added' ;;
    fix:*|fix\(*|bugfix:*|hotfix:*|*fix*|*bug*|*repair*) printf 'fixed' ;;
    remove:*|remove\(*|removed:*|delete:*|delete\(*|drop:*|drop\(*|*remove*|*delete*) printf 'removed' ;;
    refactor:*|refactor\(*|change:*|change\(*|changed:*|update:*|update\(*|perf:*|perf\(*|docs:*|docs\(*|style:*|style\(*|test:*|test\(*|chore:*|chore\(*) printf 'changed' ;;
    *) printf 'changed' ;;
  esac
}

for commit in "${commits[@]}"; do
  subject="${commit%$'\t'*}"
  sha="${commit##*$'\t'}"
  append_item "$(categorize "$subject")" "$subject" "$sha"
done

write_section() {
  local title="$1"
  shift
  local items=("$@")

  printf '### %s\n' "$title"
  if [ "${#items[@]}" -eq 0 ]; then
    printf -- '- No changes.\n\n'
    return
  fi

  local item
  for item in "${items[@]}"; do
    printf -- '- %s\n' "$item"
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated for `%s` %s on %s.\n\n' "$repo_name" "$since_label" "$generated_at"
  printf '## Unreleased\n\n'
  write_section 'Added' "${added[@]}"
  write_section 'Fixed' "${fixed[@]}"
  write_section 'Changed' "${changed[@]}"
  write_section 'Removed' "${removed[@]}"
} > "$output_file"

echo "Wrote ${output_file} with ${#commits[@]} commit(s) from ${commit_range}."
