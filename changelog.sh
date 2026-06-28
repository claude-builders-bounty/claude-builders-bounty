#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="$latest_tag..HEAD"
  range_label="since $latest_tag"
else
  range="HEAD"
  range_label="for all commits"
fi

commit_log="$(git log "$range" --pretty=format:'%s' --no-merges)"
release_date="$(date +%Y-%m-%d)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

add_entry() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ ^(feat|feature|add|added)(\\(.+\\))?: ]]; then
    added+=("$subject")
  elif [[ "$lower" =~ ^(fix|fixed|bugfix|hotfix)(\\(.+\\))?: ]]; then
    fixed+=("$subject")
  elif [[ "$lower" =~ ^(remove|removed|delete|deleted)(\\(.+\\))?: ]]; then
    removed+=("$subject")
  elif [[ "$lower" =~ ^(refactor|change|changed|update|updated|perf|docs|test|build|ci|chore)(\\(.+\\))?: ]]; then
    changed+=("$subject")
  else
    changed+=("$subject")
  fi
}

if [[ -n "$commit_log" ]]; then
  while IFS= read -r subject; do
    [[ -z "$subject" ]] && continue
    add_entry "$subject"
  done <<< "$commit_log"
fi

write_section() {
  local title="$1"
  shift
  local -a entries=("$@")

  printf '### %s\n\n' "$title"
  if ((${#entries[@]} == 0)); then
    printf -- '- No changes.\n\n'
    return
  fi

  local entry
  for entry in "${entries[@]}"; do
    printf -- '- %s\n' "$entry"
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$release_date"
  printf '_Generated from git history %s._\n\n' "$range_label"
  write_section "Added" "${added[@]+"${added[@]}"}"
  write_section "Fixed" "${fixed[@]+"${fixed[@]}"}"
  write_section "Changed" "${changed[@]+"${changed[@]}"}"
  write_section "Removed" "${removed[@]+"${removed[@]}"}"
} > "$output_file"

echo "Wrote $output_file"
