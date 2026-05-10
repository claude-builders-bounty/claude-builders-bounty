#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="$last_tag..HEAD"
  range_label="since $last_tag"
else
  range="HEAD"
  range_label="from repository history"
fi

version_label="${CHANGELOG_VERSION:-Unreleased}"
generated_date="$(date +%Y-%m-%d)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

normalize_subject() {
  local subject="$1"
  printf '%s' "$subject" | sed -E 's/^(feat|feature|fix|bugfix|hotfix|repair|chore|refactor|perf|docs?|remove|removed|delete|deleted|drop|dropped)(\([^)]*\))?!?:[[:space:]]*//I'
}

add_entry() {
  local category="$1"
  local subject="$2"
  local hash="$3"
  local entry="- $(normalize_subject "$subject") ($hash)"

  case "$category" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
}

categorize_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat!:*|feat\(*|feature:*|feature!:*|add:*|added:*)
      printf 'added'
      ;;
    fix:*|fix!:*|fix\(*|bugfix:*|bugfix!:*|hotfix:*|repair:*)
      printf 'fixed'
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|remove!:*|delete!:*)
      printf 'removed'
      ;;
    *)
      printf 'changed'
      ;;
  esac
}

while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" ]] && continue
  hash="${line%%$'\t'*}"
  subject="${line#*$'\t'}"
  category="$(categorize_commit "$subject")"
  add_entry "$category" "$subject" "$hash"
done < <(git log "$range" --no-merges --pretty=format:'%h%x09%s')

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title"
  if [[ ${#entries[@]} -eq 0 ]]; then
    printf -- '- None\n\n'
  else
    printf '%s\n' "${entries[@]}"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes are grouped from git commits %s.\n\n' "$range_label"
  printf '## %s - %s\n\n' "$version_label" "$generated_date"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$output_file"

echo "Wrote $output_file using commits $range_label."
