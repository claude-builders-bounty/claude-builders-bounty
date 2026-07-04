#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [ -n "$latest_tag" ]; then
  revision_range="$latest_tag..HEAD"
  scope="since $latest_tag"
else
  revision_range="HEAD"
  scope="from the first commit"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added_file="$tmp_dir/added"
fixed_file="$tmp_dir/fixed"
changed_file="$tmp_dir/changed"
removed_file="$tmp_dir/removed"
touch "$added_file" "$fixed_file" "$changed_file" "$removed_file"

commit_count=0

while IFS=$'\t' read -r hash subject || [ -n "${hash:-}" ]; do
  [ -n "${hash:-}" ] || continue
  commit_count=$((commit_count + 1))

  lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  entry="- $subject (\`$hash\`)"

  case "$lower_subject" in
    feat:*|feat\(*|add:*|add\ *|added\ *|create:*|create\ *)
      printf '%s\n' "$entry" >> "$added_file"
      ;;
    fix:*|fix\(*|fixed\ *|bug:*|bugfix:*|patch:*)
      printf '%s\n' "$entry" >> "$fixed_file"
      ;;
    remove:*|remove\ *|removed\ *|delete:*|delete\ *|drop:*|drop\ *)
      printf '%s\n' "$entry" >> "$removed_file"
      ;;
    *)
      printf '%s\n' "$entry" >> "$changed_file"
      ;;
  esac
done < <(git log --reverse --pretty=format:'%h%x09%s' "$revision_range")

write_section() {
  section_title="$1"
  section_file="$2"

  printf '\n## %s\n\n' "$section_title" >> "$output_file"
  if [ -s "$section_file" ]; then
    cat "$section_file" >> "$output_file"
  else
    printf '_No entries._\n' >> "$output_file"
  fi
}

{
  printf '# Changelog\n\n'
  printf 'Generated on %s for commits %s.\n' "$(date +%Y-%m-%d)" "$scope"
  if [ "$commit_count" -eq 0 ]; then
    printf '\nNo commits found for this range.\n'
  fi
} > "$output_file"

if [ "$commit_count" -gt 0 ]; then
  write_section "Added" "$added_file"
  write_section "Fixed" "$fixed_file"
  write_section "Changed" "$changed_file"
  write_section "Removed" "$removed_file"
fi

echo "Wrote $output_file from $commit_count commit(s)."
