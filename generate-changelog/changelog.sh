#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "generate-changelog: run this script inside a Git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$latest_tag" ]; then
  commit_range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  commit_range="HEAD"
  range_label="from all commits"
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "generate-changelog: this repository has no commits yet." >&2
  exit 1
fi

declare -a added_entries=()
declare -a fixed_entries=()
declare -a changed_entries=()
declare -a removed_entries=()

clean_subject() {
  printf '%s' "$1" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//'
}

append_commit() {
  subject="$1"
  short_hash="$2"
  lowered="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  entry="- $(clean_subject "$subject") (${short_hash})"

  case "$lowered" in
    feat:*|feat!:*|feat\(*|feature:*|feature\(*|add:*|add\(*|added:*|create:*|create\(*|created:*)
      added_entries+=("$entry")
      ;;
    fix:*|fix!:*|fix\(*|fixed:*|bug:*|bug\(*|resolve:*|resolve\(*|resolved:*|repair:*|repair\(*)
      fixed_entries+=("$entry")
      ;;
    remove:*|remove\(*|removed:*|delete:*|delete\(*|deleted:*|drop:*|drop\(*|dropped:*|deprecate:*|deprecate\(*|deprecated:*)
      removed_entries+=("$entry")
      ;;
    change:*|change\(*|changed:*|refactor:*|refactor\(*|perf:*|perf\(*|docs:*|docs\(*|test:*|test\(*|build:*|build\(*|ci:*|ci\(*|chore:*|chore\(*|update:*|update\(*|updated:*|improve:*|improve\(*|improved:*)
      changed_entries+=("$entry")
      ;;
    *)
      changed_entries+=("$entry")
      ;;
  esac
}

while IFS=$'\t' read -r subject short_hash; do
  if [ -n "$subject" ]; then
    append_commit "$subject" "$short_hash"
  fi
done < <(git log --reverse --no-merges --format='%s%x09%h' "$commit_range")

write_section() {
  title="$1"
  shift
  printf '### %s\n\n' "$title"

  if [ "$#" -eq 0 ]; then
    printf '_No changes._\n\n'
    return
  fi

  for entry in "$@"; do
    printf '%s\n' "$entry"
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased\n\n'
  printf '_Generated from Git history %s._\n\n' "$range_label"
  write_section "Added" "${added_entries[@]+"${added_entries[@]}"}"
  write_section "Fixed" "${fixed_entries[@]+"${fixed_entries[@]}"}"
  write_section "Changed" "${changed_entries[@]+"${changed_entries[@]}"}"
  write_section "Removed" "${removed_entries[@]+"${removed_entries[@]}"}"
} > "$output_file"

echo "Generated ${output_file} ${range_label}."
