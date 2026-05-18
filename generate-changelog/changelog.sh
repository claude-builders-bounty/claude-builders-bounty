#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
fetch_tags=1

usage() {
  printf 'Usage: bash changelog.sh [--output PATH] [--no-fetch]\n'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output|-o)
      if [ "${2:-}" = "" ]; then
        printf 'Missing value for %s\n' "$1" >&2
        exit 2
      fi
      output_file="$2"
      shift 2
      ;;
    --no-fetch)
      fetch_tags=0
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf 'This script must be run inside a git repository.\n' >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [ "$fetch_tags" -eq 1 ]; then
  git fetch --tags --quiet 2>/dev/null || true
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$last_tag" ]; then
  range="${last_tag}..HEAD"
  base_label="$last_tag"
else
  range="HEAD"
  base_label="repository start"
fi

today="$(date +%Y-%m-%d)"
repo_name="$(basename "$repo_root")"
commit_count="$(git rev-list --count --no-merges "$range" 2>/dev/null || printf '0')"

added_file="$(mktemp)"
fixed_file="$(mktemp)"
changed_file="$(mktemp)"
removed_file="$(mktemp)"
trap 'rm -f "$added_file" "$fixed_file" "$changed_file" "$removed_file"' EXIT

append_commit() {
  category_file="$1"
  subject="$2"
  sha="$3"
  author="$4"

  printf -- '- %s (`%s`, %s)\n' "$subject" "$sha" "$author" >> "$category_file"
}

categorize_subject() {
  subject_lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject_lower" in
    feat:*|feat\(*|feature:*|add:*|added:*|new:*)
      printf '%s' "$added_file"
      ;;
    fix:*|fix\(*|fixed:*|bug:*|bugfix:*|resolve:*|resolved:*|patch:*)
      printf '%s' "$fixed_file"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*)
      printf '%s' "$removed_file"
      ;;
    *)
      printf '%s' "$changed_file"
      ;;
  esac
}

while IFS=$'\037' read -r subject sha author; do
  [ -n "${subject:-}" ] || continue
  category_file="$(categorize_subject "$subject")"
  append_commit "$category_file" "$subject" "$sha" "$author"
done < <(git log --no-merges --reverse --format='%s%x1f%h%x1f%an' "$range")

write_section() {
  title="$1"
  file="$2"

  printf '### %s\n\n' "$title"
  if [ -s "$file" ]; then
    cat "$file"
  else
    printf -- '- No changes.\n'
  fi
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes for `%s` since `%s` are listed below.\n\n' "$repo_name" "$base_label"
  printf '## Unreleased - %s\n\n' "$today"
  printf '_Generated from %s commit(s)._\n\n' "$commit_count"
  write_section "Added" "$added_file"
  write_section "Fixed" "$fixed_file"
  write_section "Changed" "$changed_file"
  write_section "Removed" "$removed_file"
} > "$output_file"

printf 'Wrote %s from commits since %s.\n' "$output_file" "$base_label"
