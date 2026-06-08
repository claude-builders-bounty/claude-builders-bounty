#!/usr/bin/env bash
set -euo pipefail

output_path="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  commit_label="commits since ${last_tag}"
else
  range="HEAD"
  commit_label="all reachable commits"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added="$tmp_dir/added"
fixed="$tmp_dir/fixed"
changed="$tmp_dir/changed"
removed="$tmp_dir/removed"
touch "$added" "$fixed" "$changed" "$removed"

categorize_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    remove*|removed*|delete*|deleted*|drop*|dropped*|deprecat*)
      printf 'Removed'
      ;;
    fix*|bug*|patch*|hotfix*|repair*)
      printf 'Fixed'
      ;;
    feat*|add*|added*|create*|initial*)
      printf 'Added'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

append_commit() {
  local category="$1"
  local line="$2"

  case "$category" in
    Added) printf '%s\n' "$line" >>"$added" ;;
    Fixed) printf '%s\n' "$line" >>"$fixed" ;;
    Removed) printf '%s\n' "$line" >>"$removed" ;;
    *) printf '%s\n' "$line" >>"$changed" ;;
  esac
}

while IFS=$'\t' read -r subject hash author date || [[ -n "${subject:-}" ]]; do
  [[ -z "${subject:-}" ]] && continue
  category="$(categorize_commit "$subject")"
  append_commit "$category" "- ${subject} (${hash}, ${date}, ${author})"
done < <(git log --no-merges --date=short --pretty=format:'%s%x09%h%x09%an%x09%ad' "$range")

today="$(date +%Y-%m-%d)"
{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$today"
  printf '_Generated from %s._\n\n' "$commit_label"

  for section in Added Fixed Changed Removed; do
    printf '### %s\n\n' "$section"
    section_file="$tmp_dir/$(printf '%s' "$section" | tr '[:upper:]' '[:lower:]')"
    if [[ -s "$section_file" ]]; then
      cat "$section_file"
    else
      printf '%s\n' '- None'
    fi
    printf '\n'
  done
} >"$output_path"

printf 'Generated %s using %s.\n' "$output_path" "$commit_label"
