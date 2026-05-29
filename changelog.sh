#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required." >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run this script inside a git repository." >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [ -n "$last_tag" ]; then
  range="${last_tag}..HEAD"
  range_label="since ${last_tag}"
else
  range="HEAD"
  range_label="from project history"
fi

commit_count="$(git rev-list --count "$range" 2>/dev/null || echo 0)"
today="$(date +%Y-%m-%d)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()
declare -a uncategorized=()

normalize_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#*) }"
  printf '%s' "$subject"
}

append_commit() {
  local bucket="$1"
  local subject="$2"
  local hash="$3"
  local line="- $(normalize_subject "$subject") (${hash})"

  case "$bucket" in
    added) added+=("$line") ;;
    fixed) fixed+=("$line") ;;
    changed) changed+=("$line") ;;
    removed) removed+=("$line") ;;
    *) uncategorized+=("$line") ;;
  esac
}

while IFS=$'\t' read -r hash subject || [ -n "${hash:-}${subject:-}" ]; do
  [ -z "${hash:-}" ] && continue
  lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower_subject" in
    feat:*|feat\(*|add:*|added:*|create:*|implement:*)
      append_commit "added" "$subject" "$hash"
      ;;
    fix:*|fix\(*|bugfix:*|hotfix:*|repair:*|resolve:*)
      append_commit "fixed" "$subject" "$hash"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*)
      append_commit "removed" "$subject" "$hash"
      ;;
    change:*|changed:*|refactor:*|refactor\(*|perf:*|perf\(*|docs:*|docs\(*|test:*|test\(*|ci:*|ci\(*|build:*|build\(*|chore:*|chore\(*)
      append_commit "changed" "$subject" "$hash"
      ;;
    *)
      uncategorized+=("- ${subject} (${hash})")
      ;;
  esac
done < <(git log "$range" --no-merges --pretty=format:'%h%x09%s')

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title"
  if [ "${#entries[@]}" -eq 0 ]; then
    printf -- '- No changes.\n\n'
    return
  fi

  printf '%s\n' "${entries[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$today"
  printf '_Generated %s. Commit count: %s._\n\n' "$range_label" "$commit_count"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"

  if [ "${#uncategorized[@]}" -gt 0 ]; then
    write_section "Uncategorized" "${uncategorized[@]}"
  fi
} > "$OUTPUT_FILE"

echo "Generated ${OUTPUT_FILE} ${range_label}."
