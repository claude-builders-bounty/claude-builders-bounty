#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "generate-changelog: run this inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  heading="Unreleased"
else
  range="HEAD"
  heading="Unreleased"
fi

mapfile -t commits < <(git log "$range" --pretty=format:%s --no-merges)

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

trim() {
  local value="$*"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

sentence_case() {
  local value
  value="$(trim "$*")"
  value="${value#*:}"
  value="$(trim "$value")"
  if [[ -z "$value" ]]; then
    return
  fi
  printf '%s%s' "$(tr '[:lower:]' '[:upper:]' <<<"${value:0:1}")" "${value:1}"
}

add_commit() {
  local subject="$1"
  local lower
  local item
  lower="$(tr '[:upper:]' '[:lower:]' <<<"$subject")"
  item="$(sentence_case "$subject")"
  if [[ -z "$item" ]]; then
    return
  fi

  case "$lower" in
    feat:*|feature:*|add:*|added:*)
      added+=("$item")
      ;;
    fix:*|fixed:*|bugfix:*|hotfix:*)
      fixed+=("$item")
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*)
      removed+=("$item")
      ;;
    *)
      changed+=("$item")
      ;;
  esac
}

for commit in "${commits[@]}"; do
  add_commit "$commit"
done

write_section() {
  local title="$1"
  local empty_label="$2"
  shift
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title" >>"$output_file"
  if (( ${#entries[@]} == 0 )); then
    printf -- '- No %s detected.\n\n' "$empty_label" >>"$output_file"
    return
  fi

  for entry in "${entries[@]}"; do
    printf -- '- %s\n' "$entry" >>"$output_file"
  done
  printf '\n' >>"$output_file"
}

{
  printf '# Changelog\n\n'
  printf '## %s\n\n' "$heading"
  if [[ -n "$latest_tag" ]]; then
    printf '_Changes since `%s`._\n\n' "$latest_tag"
  else
    printf '_Generated from all commits because no git tags were found._\n\n'
  fi
} >"$output_file"

write_section "Added" "additions" "${added[@]}"
write_section "Fixed" "fixes" "${fixed[@]}"
write_section "Changed" "changes" "${changed[@]}"
write_section "Removed" "removals" "${removed[@]}"

echo "Generated $output_file from ${#commits[@]} commits."
