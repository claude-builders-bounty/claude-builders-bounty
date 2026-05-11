#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [repo-path] [output-file]

Generates a structured CHANGELOG.md from git commits since the latest tag.

Arguments:
  repo-path     Git repository to inspect. Defaults to current directory.
  output-file   Changelog file to write. Defaults to CHANGELOG.md.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

repo_path="${1:-.}"
output_file="${2:-CHANGELOG.md}"

if ! git -C "$repo_path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: '$repo_path' is not a git repository." >&2
  exit 1
fi

latest_tag="$(git -C "$repo_path" describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$latest_tag" ]]; then
  revision_range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  revision_range="HEAD"
  range_label="from repository history"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added_file="$tmp_dir/added"
fixed_file="$tmp_dir/fixed"
changed_file="$tmp_dir/changed"
removed_file="$tmp_dir/removed"
touch "$added_file" "$fixed_file" "$changed_file" "$removed_file"

categorize_commit() {
  local subject_lower="$1"

  case "$subject_lower" in
    revert:*|remove:*|removed:*|delete:*|deleted:*|drop:*|breaking:*|*!:*)
      echo "Removed"
      ;;
    fix:*|fixed:*|bug:*|bugfix:*|hotfix:*|*fix*|*bug*)
      echo "Fixed"
      ;;
    feat:*|feature:*|add:*|added:*|new:*|*add*|*introduce*)
      echo "Added"
      ;;
    *)
      echo "Changed"
      ;;
  esac
}

commit_count=0

while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" ]] && continue

  commit_count=$((commit_count + 1))
  subject_lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  category="$(categorize_commit "$subject_lower")"
  line="- ${subject} (${hash})"

  case "$category" in
    Added) printf '%s\n' "$line" >> "$added_file" ;;
    Fixed) printf '%s\n' "$line" >> "$fixed_file" ;;
    Changed) printf '%s\n' "$line" >> "$changed_file" ;;
    Removed) printf '%s\n' "$line" >> "$removed_file" ;;
  esac
done < <(git -C "$repo_path" log "$revision_range" --pretty=format:'%h%x09%s' --no-merges)

write_section() {
  local heading="$1"
  local file="$2"

  printf '\n## %s\n\n' "$heading"
  if [[ -s "$file" ]]; then
    cat "$file"
  else
    printf -- '- No changes.\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'Generated on %s for commits %s.\n' "$(date +%Y-%m-%d)" "$range_label"

  if [[ "$commit_count" -eq 0 ]]; then
    printf '\nNo commits found for this range.\n'
  else
    write_section "Added" "$added_file"
    write_section "Fixed" "$fixed_file"
    write_section "Changed" "$changed_file"
    write_section "Removed" "$removed_file"
  fi
} > "$output_file"

echo "Wrote ${output_file} with ${commit_count} commit(s)."
