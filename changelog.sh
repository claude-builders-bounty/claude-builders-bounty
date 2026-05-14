#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  commit_range="$last_tag..HEAD"
  range_label="since $last_tag"
else
  commit_range="HEAD"
  range_label="from repository history"
fi

tmp_file="$(mktemp)"
added_file="$(mktemp)"
fixed_file="$(mktemp)"
changed_file="$(mktemp)"
removed_file="$(mktemp)"
trap 'rm -f "$tmp_file" "$added_file" "$fixed_file" "$changed_file" "$removed_file"' EXIT

categorize_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|feature:*|add:*|added:*|new:*)
      printf '%s\n' "Added"
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*)
      printf '%s\n' "Fixed"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*)
      printf '%s\n' "Removed"
      ;;
    *)
      if [[ "$lower" == *"remove"* || "$lower" == *"delete"* || "$lower" == *"drop "* ]]; then
        printf '%s\n' "Removed"
      elif [[ "$lower" == *"fix"* || "$lower" == *"bug"* ]]; then
        printf '%s\n' "Fixed"
      elif [[ "$lower" == *"add"* || "$lower" == *"implement"* || "$lower" == *"introduce"* ]]; then
        printf '%s\n' "Added"
      else
        printf '%s\n' "Changed"
      fi
      ;;
  esac
}

append_entry() {
  local file="$1"
  local hash="$2"
  local subject="$3"

  printf -- '- %s (%s)\n' "$subject" "$hash" >>"$file"
}

while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}" ]]; do
  [[ -n "${hash:-}" ]] || continue

  category="$(categorize_commit "$subject")"
  case "$category" in
    Added)
      append_entry "$added_file" "$hash" "$subject"
      ;;
    Fixed)
      append_entry "$fixed_file" "$hash" "$subject"
      ;;
    Removed)
      append_entry "$removed_file" "$hash" "$subject"
      ;;
    *)
      append_entry "$changed_file" "$hash" "$subject"
      ;;
  esac
done < <(git log "$commit_range" --pretty=format:'%h%x09%s')

write_section() {
  local heading="$1"
  local file="$2"

  printf '### %s\n' "$heading" >>"$tmp_file"
  if [[ -s "$file" ]]; then
    cat "$file" >>"$tmp_file"
  else
    printf -- '- Nothing.\n' >>"$tmp_file"
  fi
  printf '\n' >>"$tmp_file"
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$(date +%Y-%m-%d)"
  printf '_Generated from commits %s._\n\n' "$range_label"
} >"$tmp_file"

write_section "Added" "$added_file"
write_section "Fixed" "$fixed_file"
write_section "Changed" "$changed_file"
write_section "Removed" "$removed_file"

mv "$tmp_file" "$output_file"
trap - EXIT
rm -f "$added_file" "$fixed_file" "$changed_file" "$removed_file"

echo "Generated $output_file"
