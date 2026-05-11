#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
since_ref=""
dry_run=0

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--output CHANGELOG.md] [--since v1.2.0] [--dry-run]

Generates a structured CHANGELOG.md from commits since the latest git tag.
If the repository has no tags, all commits are included.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      output_file="$2"
      shift 2
      ;;
    --since)
      [[ $# -ge 2 ]] || { echo "Missing value for --since" >&2; exit 2; }
      since_ref="$2"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
}

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
today="$(date +%Y-%m-%d)"

if [[ -z "$since_ref" ]]; then
  since_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$since_ref" ]]; then
  if ! git rev-parse --verify --quiet "$since_ref^{commit}" >/dev/null; then
    echo "Reference not found: $since_ref" >&2
    exit 1
  fi
  range_label="$since_ref..HEAD"
  git_range=("$since_ref..HEAD")
else
  range_label="all commits"
  git_range=("HEAD")
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added="$tmp_dir/added"
fixed="$tmp_dir/fixed"
changed="$tmp_dir/changed"
removed="$tmp_dir/removed"
: > "$added"
: > "$fixed"
: > "$changed"
: > "$removed"

clean_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#*:}"
  printf '%s' "$subject"
}

category_for() {
  local subject lowered
  subject="$1"
  lowered="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lowered" =~ ^(feat|feature|add|create|implement|introduce)(\(.+\))?!?: ]]; then
    printf 'added'
  elif [[ "$lowered" =~ ^(fix|bug|bugfix|patch|resolve|repair)(\(.+\))?!?: ]]; then
    printf 'fixed'
  elif [[ "$lowered" =~ ^(remove|delete|drop|deprecate|prune)(\(.+\))?!?: ]]; then
    printf 'removed'
  elif [[ "$lowered" =~ (remove|delete|drop|deprecat|prune) ]]; then
    printf 'removed'
  elif [[ "$lowered" =~ (fix|bug|resolve|repair|correct) ]]; then
    printf 'fixed'
  elif [[ "$lowered" =~ (add|create|implement|introduce|new ) ]]; then
    printf 'added'
  else
    printf 'changed'
  fi
}

while IFS=$'\t' read -r hash short_hash commit_date subject || [[ -n "${hash:-}" ]]; do
  [[ -n "${hash:-}" ]] || continue
  category="$(category_for "$subject")"
  cleaned="$(clean_subject "$subject")"
  line="- ${cleaned} (${short_hash}, ${commit_date})"

  case "$category" in
    added) printf '%s\n' "$line" >> "$added" ;;
    fixed) printf '%s\n' "$line" >> "$fixed" ;;
    removed) printf '%s\n' "$line" >> "$removed" ;;
    *) printf '%s\n' "$line" >> "$changed" ;;
  esac
done < <(git log "${git_range[@]}" --reverse --date=short --pretty=format:'%H%x09%h%x09%ad%x09%s')

write_section() {
  local title="$1"
  local file="$2"
  if [[ -s "$file" ]]; then
    printf '\n### %s\n\n' "$title"
    cat "$file"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git history for `%s`.\n\n' "$repo_name"
  printf '## Unreleased - %s\n\n' "$today"
  printf '_Commit range: %s_\n' "$range_label"
  write_section "Added" "$added"
  write_section "Fixed" "$fixed"
  write_section "Changed" "$changed"
  write_section "Removed" "$removed"
} > "$tmp_dir/CHANGELOG.md"

if [[ ! -s "$added" && ! -s "$fixed" && ! -s "$changed" && ! -s "$removed" ]]; then
  {
    printf '# Changelog\n\n'
    printf '## Unreleased - %s\n\n' "$today"
    printf 'No commits found for range `%s`.\n' "$range_label"
  } > "$tmp_dir/CHANGELOG.md"
fi

if [[ "$dry_run" -eq 1 ]]; then
  cat "$tmp_dir/CHANGELOG.md"
else
  cp "$tmp_dir/CHANGELOG.md" "$output_file"
  printf 'Wrote %s\n' "$output_file"
fi
