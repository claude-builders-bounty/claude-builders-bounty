#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  revision_range="${latest_tag}..HEAD"
  scope_text="Changes since ${latest_tag}"
else
  revision_range="HEAD"
  scope_text="All commits"
fi

commit_count="$(git rev-list --count "$revision_range" 2>/dev/null || echo 0)"
if [[ "$commit_count" == "0" ]]; then
  {
    echo "# Changelog"
    echo
    echo "_No commits found for ${scope_text}._"
  } > "$output_file"
  echo "Wrote ${output_file}"
  exit 0
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added="$tmp_dir/added.md"
fixed="$tmp_dir/fixed.md"
changed="$tmp_dir/changed.md"
removed="$tmp_dir/removed.md"
: > "$added"
: > "$fixed"
: > "$changed"
: > "$removed"

categorize_commit() {
  local subject_lower="$1"

  case "$subject_lower" in
    feat:*|feat\(*|feature:*|add:*|added:*) echo "$added" ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*) echo "$fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*) echo "$removed" ;;
    *) echo "$changed" ;;
  esac
}

while IFS=$'\t' read -r hash date subject || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" ]] && continue
  clean_subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
  subject_lower="$(printf '%s' "$clean_subject" | tr '[:upper:]' '[:lower:]')"
  target_file="$(categorize_commit "$subject_lower")"
  printf -- "- %s (%s, %s)\n" "$clean_subject" "$hash" "$date" >> "$target_file"
done < <(git log "$revision_range" --no-merges --date=short --pretty=format:'%h%x09%ad%x09%s')

write_section() {
  local title="$1"
  local file="$2"

  echo "## ${title}"
  echo
  if [[ -s "$file" ]]; then
    cat "$file"
  else
    echo "- No ${title,,} changes."
  fi
}

{
  echo "# Changelog"
  echo
  echo "_Generated on $(date -u +%Y-%m-%d) from ${scope_text}._"
  echo
  write_section "Added" "$added"
  echo
  write_section "Fixed" "$fixed"
  echo
  write_section "Changed" "$changed"
  echo
  write_section "Removed" "$removed"
} > "$output_file"

echo "Wrote ${output_file}"
