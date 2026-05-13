#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/generate-changelog.sh [options]

Generate a structured CHANGELOG.md from git history.

Options:
  -o, --output FILE   Write changelog to FILE (default: CHANGELOG.md)
      --since REF     Start after REF instead of the latest tag
      --title TEXT    Changelog title (default: Changelog)
  -h, --help          Show this help message

Examples:
  scripts/generate-changelog.sh
  scripts/generate-changelog.sh --since v1.2.0 --output RELEASE_NOTES.md
USAGE
}

output_file="CHANGELOG.md"
since_ref=""
title="Changelog"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      output_file="${2:-}"
      [[ -n "$output_file" ]] || { echo "Missing value for $1" >&2; exit 2; }
      shift 2
      ;;
    --since)
      since_ref="${2:-}"
      [[ -n "$since_ref" ]] || { echo "Missing value for $1" >&2; exit 2; }
      shift 2
      ;;
    --title)
      title="${2:-}"
      [[ -n "$title" ]] || { echo "Missing value for $1" >&2; exit 2; }
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "generate-changelog must be run inside a git repository." >&2
  exit 1
fi

latest_tag=""
if [[ -z "$since_ref" ]]; then
  latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
else
  latest_tag="$since_ref"
fi

range_label="all history"
if [[ -n "$latest_tag" ]]; then
  range_label="changes since ${latest_tag}"
fi

repo_url="$(git config --get remote.origin.url || true)"
commit_base_url=""
compare_url=""
if [[ "$repo_url" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
  owner="${BASH_REMATCH[1]}"
  repo="${BASH_REMATCH[2]}"
  commit_base_url="https://github.com/${owner}/${repo}/commit"
  if [[ -n "$latest_tag" ]]; then
    compare_url="https://github.com/${owner}/${repo}/compare/${latest_tag}...HEAD"
  fi
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

breaking_file="$tmp_dir/breaking.md"
added_file="$tmp_dir/added.md"
fixed_file="$tmp_dir/fixed.md"
changed_file="$tmp_dir/changed.md"
removed_file="$tmp_dir/removed.md"
other_file="$tmp_dir/other.md"
: >"$breaking_file"
: >"$added_file"
: >"$fixed_file"
: >"$changed_file"
: >"$removed_file"
: >"$other_file"

breaking_regex='^[a-zA-Z]+(\([^)]+\))?!:'
feature_regex='^feat(\([^)]+\))?:'
fix_regex='^fix(\([^)]+\))?:'
removed_regex='^(remove|delete|drop)(\([^)]+\))?:'
changed_regex='^(change|changed|docs?|perf|refactor|test(s)?|chore|ci|build|style)(\([^)]+\))?:'

format_entry() {
  local hash="$1"
  local date="$2"
  local subject="$3"
  local author="$4"
  local short_hash
  short_hash="$(git rev-parse --short "$hash")"

  if [[ -n "$commit_base_url" ]]; then
    printf -- "- %s ([%s](%s/%s), %s, %s)\n" "$subject" "$short_hash" "$commit_base_url" "$hash" "$date" "$author"
  else
    printf -- "- %s (%s, %s, %s)\n" "$subject" "$short_hash" "$date" "$author"
  fi
}

append_entry() {
  local target_file="$1"
  local hash="$2"
  local date="$3"
  local subject="$4"
  local author="$5"
  format_entry "$hash" "$date" "$subject" "$author" >>"$target_file"
}

commit_count=0
if [[ -n "$latest_tag" ]]; then
  git_log_command=(git log "${latest_tag}..HEAD" --no-merges --date=short --pretty=format:'%H%x1f%ad%x1f%s%x1f%an')
else
  git_log_command=(git log --no-merges --date=short --pretty=format:'%H%x1f%ad%x1f%s%x1f%an')
fi

while IFS=$'\037' read -r hash date subject author; do
  [[ -n "${hash:-}" ]] || continue
  commit_count=$((commit_count + 1))

  if [[ "$subject" =~ BREAKING[[:space:]]CHANGE || "$subject" =~ $breaking_regex || "$subject" =~ [Bb]reaking ]]; then
    append_entry "$breaking_file" "$hash" "$date" "$subject" "$author"
  elif [[ "$subject" =~ $removed_regex || "$subject" =~ [Rr]emove || "$subject" =~ [Dd]elete ]]; then
    append_entry "$removed_file" "$hash" "$date" "$subject" "$author"
  elif [[ "$subject" =~ $feature_regex ]]; then
    append_entry "$added_file" "$hash" "$date" "$subject" "$author"
  elif [[ "$subject" =~ $fix_regex ]]; then
    append_entry "$fixed_file" "$hash" "$date" "$subject" "$author"
  elif [[ "$subject" =~ $changed_regex ]]; then
    append_entry "$changed_file" "$hash" "$date" "$subject" "$author"
  else
    append_entry "$other_file" "$hash" "$date" "$subject" "$author"
  fi
done < <("${git_log_command[@]}"; printf '\n')

write_section() {
  local heading="$1"
  local source_file="$2"

  if [[ -s "$source_file" ]]; then
    {
      printf '\n### %s\n\n' "$heading"
      cat "$source_file"
    } >>"$output_file"
  fi
}

{
  printf '# %s\n\n' "$title"
  printf 'Generated on %s from %s.\n' "$(date +%Y-%m-%d)" "$range_label"
  if [[ -n "$compare_url" ]]; then
    printf '\n[Full diff](%s)\n' "$compare_url"
  fi
  printf '\n## Unreleased\n'
} >"$output_file"

if [[ "$commit_count" -eq 0 ]]; then
  printf '\nNo changes found.\n' >>"$output_file"
else
  write_section "Breaking Changes" "$breaking_file"
  write_section "Added" "$added_file"
  write_section "Fixed" "$fixed_file"
  write_section "Changed" "$changed_file"
  write_section "Removed" "$removed_file"
  write_section "Other Changes" "$other_file"
fi

echo "Wrote ${output_file} (${commit_count} commits)."
