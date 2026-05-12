#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  commit_range="${last_tag}..HEAD"
  range_label="since ${last_tag}"
else
  commit_range="HEAD"
  range_label="for all commits"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

normalize_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#*:}"
  subject="${subject#"${subject%%[![:space:]]*}"}"
  subject="${subject%"${subject##*[![:space:]]}"}"
  printf '%s' "$subject"
}

add_commit() {
  local subject="$1"
  local normalized
  normalized="$(normalize_subject "$subject")"
  [[ -z "$normalized" ]] && normalized="$subject"

  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|add:*|added:*|new:*)
      added+=("$normalized")
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|patch:*)
      fixed+=("$normalized")
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*)
      removed+=("$normalized")
      ;;
    change:*|changed:*|refactor:*|refactor\(*|perf:*|perf\(*|docs:*|docs\(*|chore:*|chore\(*|build:*|build\(*|ci:*|ci\(*|test:*|test\(*|style:*|style\(*)
      changed+=("$normalized")
      ;;
    *)
      changed+=("$normalized")
      ;;
  esac
}

while IFS= read -r commit; do
  add_commit "$commit"
done < <(git log "$commit_range" --no-merges --pretty=format:'%s' 2>/dev/null || true)

write_section() {
  local title="$1"
  local array_name="$2"
  local length
  eval "length=\${#${array_name}[@]}"

  printf '### %s\n\n' "$title"
  if [[ "$length" -eq 0 ]]; then
    printf -- '- No changes.\n\n'
    return
  fi

  local index=0
  local item
  while [[ "$index" -lt "$length" ]]; do
    eval "item=\${${array_name}[$index]}"
    printf -- '- %s\n' "$item"
    index=$((index + 1))
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated %s from git history %s.\n\n' "$(date +%Y-%m-%d)" "$range_label"
  write_section "Added" "added"
  write_section "Fixed" "fixed"
  write_section "Changed" "changed"
  write_section "Removed" "removed"
} > "$output_file"

echo "Wrote ${output_file}"
