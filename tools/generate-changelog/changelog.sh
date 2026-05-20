#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      output_file="${2:?missing output path}"
      shift 2
      ;;
    -h|--help)
      printf 'Usage: bash changelog.sh [--output CHANGELOG.md]\n'
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range="HEAD"
  since_label="for all commits"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

touch "$tmp_dir/Added" "$tmp_dir/Fixed" "$tmp_dir/Changed" "$tmp_dir/Removed"

categorize_subject() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|add:*|add\ *|create:*|create\ *|initial\ *)
      printf 'Added'
      ;;
    fix:*|fix\(*|bug:*|bug\ *|patch:*|patch\ *|repair:*|repair\ *)
      printf 'Fixed'
      ;;
    remove:*|remove\ *|delete:*|delete\ *|drop:*|drop\ *|deprecate:*)
      printf 'Removed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

escape_markdown() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/`/\\`/g'
}

while IFS=$'\t' read -r short_hash subject author; do
  [[ -n "$short_hash" ]] || continue
  category="$(categorize_subject "$subject")"
  safe_subject="$(escape_markdown "$subject")"
  safe_author="$(escape_markdown "$author")"
  printf -- '- %s (`%s`, %s)\n' "$safe_subject" "$short_hash" "$safe_author" \
    >> "$tmp_dir/$category"
done < <(git log --reverse --format='%h%x09%s%x09%an' "$range")

{
  printf '# Changelog\n\n'
  printf 'Generated from git history %s on %s.\n\n' \
    "$since_label" "$(date -u '+%Y-%m-%d')"

  for category in Added Fixed Changed Removed; do
    printf '## %s\n\n' "$category"
    if [[ -s "$tmp_dir/$category" ]]; then
      cat "$tmp_dir/$category"
    else
      printf -- '- No entries.\n'
    fi
    printf '\n'
  done
} > "$output_file"

printf 'Generated %s from git history %s.\n' "$output_file" "$since_label"
