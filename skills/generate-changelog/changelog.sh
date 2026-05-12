#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
}

cd "$repo_root"

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="$latest_tag..HEAD"
  range_label="$latest_tag..HEAD"
else
  range="HEAD"
  range_label="all commits"
fi

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

if ! git log "$range" --no-merges --format='%h%x09%s' > "$tmp_file"; then
  echo "error: failed to read git history for range '$range_label'" >&2
  exit 1
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

clean_subject() {
  local subject="$1"
  local prefix="${subject%%:*}"
  if [[ "$prefix" != "$subject" && "$prefix" != *" "* ]]; then
    subject="${subject#*: }"
  fi
  printf '%s' "$subject"
}

append_item() {
  local bucket="$1"
  local item="$2"

  case "$bucket" in
    added) added+=("$item") ;;
    fixed) fixed+=("$item") ;;
    removed) removed+=("$item") ;;
    *) changed+=("$item") ;;
  esac
}

categorize() {
  local subject="$1"
  local lowered
  lowered="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lowered" in
    feat:*|feature:*|add:*|added:*|create:*|implement:*|introduce:*|init:*) echo "added" ;;
    fix:*|fixed:*|bug:*|patch:*|repair:*|resolve:*|correct:*) echo "fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*) echo "removed" ;;
    refactor:*|change:*|changed:*|update:*|updated:*|improve:*|improved:*|docs:*|doc:*|test:*|tests:*|chore:*) echo "changed" ;;
    *" add "*|*" adds "*|*" added "*|add\ *|adds\ *|added\ *) echo "added" ;;
    *" fix "*|*" fixes "*|*" fixed "*|fix\ *|fixes\ *|fixed\ *) echo "fixed" ;;
    *" remove "*|*" removes "*|*" removed "*|remove\ *|removes\ *|removed\ *) echo "removed" ;;
    *) echo "changed" ;;
  esac
}

commit_count=0
while IFS=$'\t' read -r hash subject; do
  [[ -n "${hash:-}" ]] || continue
  commit_count=$((commit_count + 1))
  bucket="$(categorize "$subject")"
  item="$(clean_subject "$subject") ($hash)"
  append_item "$bucket" "$item"
done < "$tmp_file"

write_section() {
  local title="$1"
  local array_name="$2"
  local -n entries="$array_name"

  printf '## %s\n\n' "$title"
  if [[ "${#entries[@]}" -eq 0 ]]; then
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
  printf 'Generated on %s from `%s`.\n\n' "$(date -u '+%Y-%m-%d')" "$range_label"
  write_section "Added" added
  write_section "Fixed" fixed
  write_section "Changed" changed
  write_section "Removed" removed
} > CHANGELOG.md

echo "Generated CHANGELOG.md from $commit_count commits."
echo "Range: $range_label"
