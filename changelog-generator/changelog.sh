#!/usr/bin/env bash
set -euo pipefail

output="${OUTPUT:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag=""
if latest_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range="HEAD"
  since_label="from all commits"
fi

if ! git rev-list --count "${range}" >/dev/null 2>&1; then
  echo "error: unable to inspect git history for range: ${range}" >&2
  exit 1
fi

commit_count="$(git rev-list --count "${range}")"
today="$(date +%Y-%m-%d)"

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

git log "${range}" --no-merges --pretty=format:'%s%x1f%h' > "$tmp"

category_for() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    add:*|added:*|feat:*|feature:*|feat\(*|feature\(*|*' add '*|*' adds '*|*' added '*)
      printf 'Added'
      ;;
    fix:*|fixed:*|bugfix:*|hotfix:*|fix\(*|*' fix '*|*' fixes '*|*' fixed '*|*' bug '*)
      printf 'Fixed'
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|removed\(*|*' remove '*|*' removes '*|*' removed '*|*' delete '*)
      printf 'Removed'
      ;;
    change:*|changed:*|update:*|updated:*|refactor:*|docs:*|doc:*|chore:*|change\(*|update\(*|refactor\(*|docs\(*)
      printf 'Changed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

write_section() {
  local section="$1"
  local section_file="$2"

  printf '### %s\n\n' "$section"
  if [[ -s "$section_file" ]]; then
    sort -u "$section_file"
  else
    printf -- '- No changes.\n'
  fi
  printf '\n'
}

added="$(mktemp)"
fixed="$(mktemp)"
changed="$(mktemp)"
removed="$(mktemp)"
trap 'rm -f "$tmp" "$added" "$fixed" "$changed" "$removed"' EXIT

while IFS=$'\x1f' read -r subject hash || [[ -n "${subject:-}" ]]; do
  [[ -z "${subject}" ]] && continue
  category="$(category_for "$subject")"
  line="- ${subject} (${hash})"
  case "$category" in
    Added) printf '%s\n' "$line" >> "$added" ;;
    Fixed) printf '%s\n' "$line" >> "$fixed" ;;
    Removed) printf '%s\n' "$line" >> "$removed" ;;
    *) printf '%s\n' "$line" >> "$changed" ;;
  esac
done < "$tmp"

{
  printf '# Changelog\n\n'
  printf 'All notable changes are documented in this file.\n\n'
  printf '## Unreleased - %s\n\n' "$today"
  printf '_Generated from %s commit(s) %s._\n\n' "$commit_count" "$since_label"
  write_section "Added" "$added"
  write_section "Fixed" "$fixed"
  write_section "Changed" "$changed"
  write_section "Removed" "$removed"
} > "$output"

echo "Generated ${output}"
