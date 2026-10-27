#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash changelog.sh [options]

Options:
  -o, --output FILE    Output file path. Defaults to CHANGELOG.md.
  -r, --repo DIR       Git repository path. Defaults to current directory.
  -v, --version NAME   Changelog heading. Defaults to Unreleased.
  -h, --help           Show this help message.

The script reads commits since the latest git tag. If the repository has no
tags, it reads the full history.
USAGE
}

output_file="CHANGELOG.md"
repo_dir="."
version="Unreleased"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      output_file="${2:-}"
      shift 2
      ;;
    -r|--repo)
      repo_dir="${2:-}"
      shift 2
      ;;
    -v|--version)
      version="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$output_file" || -z "$repo_dir" || -z "$version" ]]; then
  echo "Missing value for an option." >&2
  usage >&2
  exit 1
fi

if ! git -C "$repo_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $repo_dir" >&2
  exit 1
fi

latest_tag=""
if latest_tag=$(git -C "$repo_dir" describe --tags --abbrev=0 2>/dev/null); then
  range="$latest_tag..HEAD"
  range_label="since $latest_tag"
else
  range="HEAD"
  range_label="from the beginning of history"
fi

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

added_file="$tmp_dir/added"
fixed_file="$tmp_dir/fixed"
changed_file="$tmp_dir/changed"
removed_file="$tmp_dir/removed"
: >"$added_file"
: >"$fixed_file"
: >"$changed_file"
: >"$removed_file"

categorize_commit() {
  local subject="$1"
  local normalized
  normalized=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')

  case "$normalized" in
    feat:*|feat\(*|add:*|add\ *|adds\ *|added:*|added\ *|*" add "*|*" adds "*|*" added "*)
      printf '%s\n' "$added_file"
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" fixed "*|*" bug "*)
      printf '%s\n' "$fixed_file"
      ;;
    remove:*|remove\ *|removed:*|removed\ *|delete:*|delete\ *|deleted:*|deleted\ *|drop:*|drop\ *|dropped:*|dropped\ *|*" remove "*|*" removes "*|*" removed "*|*" delete "*|*" deleted "*)
      printf '%s\n' "$removed_file"
      ;;
    *)
      printf '%s\n' "$changed_file"
      ;;
  esac
}

commit_count=0
while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}" ]]; do
  [[ -n "${hash:-}" ]] || continue
  commit_count=$((commit_count + 1))
  target_file=$(categorize_commit "$subject")
  printf -- '- %s (`%s`)\n' "$subject" "$hash" >>"$target_file"
done < <(git -C "$repo_dir" log --no-merges --pretty=format:'%h%x09%s' "$range")

write_section() {
  local title="$1"
  local file="$2"

  printf '### %s\n\n' "$title"
  if [[ -s "$file" ]]; then
    cat "$file"
  else
    printf -- '- No changes.\n'
  fi
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git commit history.\n\n'
  printf '## [%s] - %s\n\n' "$version" "$(date +%Y-%m-%d)"
  printf '_Commits %s._\n\n' "$range_label"

  if [[ "$commit_count" -eq 0 ]]; then
    printf 'No commits found for this release window.\n'
  else
    write_section "Added" "$added_file"
    write_section "Fixed" "$fixed_file"
    write_section "Changed" "$changed_file"
    write_section "Removed" "$removed_file"
  fi
} >"$output_file"

echo "Wrote $output_file from $commit_count commit(s) $range_label."
