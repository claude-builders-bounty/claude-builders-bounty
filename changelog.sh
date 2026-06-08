#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [output-file]

Generates a structured CHANGELOG.md from commits since the most recent git tag.
When no tag exists, it uses the full repository history.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "error: repository has no commits" >&2
  exit 1
fi

output_file="${1:-CHANGELOG.md}"
today="$(date +%Y-%m-%d)"
repo_name="$(basename "$repo_root")"
last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$last_tag" ]]; then
  revision_range="$last_tag..HEAD"
  range_label="commits since \`$last_tag\`"
else
  revision_range="HEAD"
  range_label="all commits; no git tags were found"
fi

added=""
fixed=""
changed=""
removed=""

append_line() {
  local bucket="$1"
  local subject="$2"
  local hash="$3"
  local entry="- ${subject} (${hash})"

  case "$bucket" in
    added) added+="${entry}"$'\n' ;;
    fixed) fixed+="${entry}"$'\n' ;;
    changed) changed+="${entry}"$'\n' ;;
    removed) removed+="${entry}"$'\n' ;;
  esac
}

category_for_subject() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    remove:*|remove\(*|removed:*|delete:*|delete\(*|drop:*|drop\(*|deprecate:*|deprecate\(*)
      printf 'removed'
      return
      ;;
    fix:*|fix\(*|fixed:*|bug:*|bugfix:*|patch:*|repair:*|resolve:*|resolved:*)
      printf 'fixed'
      return
      ;;
    feat:*|feat\(*|feature:*|add:*|add\(*|added:*|create:*|create\(*|implement:*|implement\(*|introduce:*|introduce\(*)
      printf 'added'
      return
      ;;
    change:*|change\(*|changed:*|update:*|update\(*|refactor:*|refactor\(*|perf:*|perf\(*|docs:*|docs\(*|test:*|test\(*|ci:*|ci\(*|build:*|build\(*|style:*|style\(*|chore:*|chore\(*)
      printf 'changed'
      return
      ;;
  esac

  if [[ "$lower" == *"remove"* || "$lower" == *"delete"* || "$lower" == *"drop"* ]]; then
    printf 'removed'
  elif [[ "$lower" == *"fix"* || "$lower" == *"bug"* || "$lower" == *"resolve"* ]]; then
    printf 'fixed'
  elif [[ "$lower" == *"add"* || "$lower" == *"create"* || "$lower" == *"implement"* || "$lower" == *"introduce"* ]]; then
    printf 'added'
  else
    printf 'changed'
  fi
}

while IFS=$'\037' read -r subject hash || [[ -n "${subject}${hash}" ]]; do
  [[ -z "${subject}${hash}" ]] && continue
  category="$(category_for_subject "$subject")"
  append_line "$category" "$subject" "$hash"
done < <(git log --no-merges --pretty=format:'%s%x1f%h' "$revision_range")

write_section() {
  local title="$1"
  local content="$2"

  {
    printf '### %s\n\n' "$title"
    if [[ -n "$content" ]]; then
      printf '%s\n' "$content"
    else
      printf -- '- No changes.\n\n'
    fi
  } >> "$output_file"
}

{
  printf '# Changelog\n\n'
  printf 'Generated on %s for `%s` from %s.\n\n' "$today" "$repo_name" "$range_label"
  printf '## Unreleased - %s\n\n' "$today"
} > "$output_file"

write_section "Added" "$added"
write_section "Fixed" "$fixed"
write_section "Changed" "$changed"
write_section "Removed" "$removed"

echo "Wrote ${output_file}"
