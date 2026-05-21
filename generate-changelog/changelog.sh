#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: changelog.sh [--output CHANGELOG.md] [--from REF] [--to REF]

Generate a structured CHANGELOG.md from commits since the last git tag.

Options:
  --output FILE  File to write. Defaults to CHANGELOG.md.
  --from REF     Starting ref/tag. Defaults to the latest reachable tag.
  --to REF       Ending ref. Defaults to HEAD.
  --help         Show this help.
USAGE
}

output_file="CHANGELOG.md"
from_ref=""
to_ref="HEAD"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output)
      if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
        echo "--output requires a file path." >&2
        exit 2
      fi
      output_file="${2:-}"
      shift 2
      ;;
    --from)
      if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
        echo "--from requires a git ref." >&2
        exit 2
      fi
      from_ref="${2:-}"
      shift 2
      ;;
    --to)
      if [ "$#" -lt 2 ] || [ -z "${2:-}" ]; then
        echo "--to requires a git ref." >&2
        exit 2
      fi
      to_ref="${2:-}"
      shift 2
      ;;
    --help|-h)
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
  echo "changelog.sh must be run inside a git repository." >&2
  exit 1
fi

if [ -z "$from_ref" ]; then
  from_ref="$(git describe --tags --abbrev=0 "$to_ref" 2>/dev/null || true)"
fi

if [ -n "$from_ref" ]; then
  range="${from_ref}..${to_ref}"
  range_label="since ${from_ref}"
else
  range="$to_ref"
  range_label="from repository history"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added_file="$tmp_dir/added"
fixed_file="$tmp_dir/fixed"
changed_file="$tmp_dir/changed"
removed_file="$tmp_dir/removed"
touch "$added_file" "$fixed_file" "$changed_file" "$removed_file"

category_for_subject() {
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  prefix="$(printf '%s' "$subject" | sed -E 's/^([a-z]+)(\([^)]*\))?(!)?:.*/\1/')"

  case "$prefix" in
    feat|add|added|create|implement)
      printf 'added'
      ;;
    fix|fixed|bugfix|hotfix|repair|resolve|resolved)
      printf 'fixed'
      ;;
    remove|removed|delete|drop|deprecate|deprecated)
      printf 'removed'
      ;;
    change|changed|refactor|docs|chore|perf|test|build|ci|style|update|improve)
      printf 'changed'
      ;;
    *)
      printf 'changed'
      ;;
  esac
}

strip_trailer() {
  printf '%s' "$1" | sed -E 's/[[:space:]]+\([0-9a-f]{7,40}\)$//'
}

git log --no-merges --date=short --pretty=format:'%h%x09%ad%x09%s' "$range" |
while IFS="$(printf '\t')" read -r sha commit_date subject || [ -n "${sha:-}" ]; do
  [ -n "$sha" ] || continue
  category="$(category_for_subject "$subject")"
  line="- ${subject} (${sha}, ${commit_date})"

  case "$category" in
    added) printf '%s\n' "$line" >> "$added_file" ;;
    fixed) printf '%s\n' "$line" >> "$fixed_file" ;;
    removed) printf '%s\n' "$line" >> "$removed_file" ;;
    changed) printf '%s\n' "$line" >> "$changed_file" ;;
  esac
done

write_section() {
  title="$1"
  file="$2"

  printf '### %s\n\n' "$title"
  if [ -s "$file" ]; then
    sed -E 's/[[:space:]]+$//' "$file"
  else
    printf '%s\n' '- No changes.'
  fi
  printf '\n\n'
}

latest_tag_label="${from_ref:-No previous tag found}"
release_label="Unreleased"
generated_on="$(date +%Y-%m-%d)"

{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git history.\n\n'
  printf '## %s - %s\n\n' "$release_label" "$generated_on"
  printf '_Generated from commits %s through %s._\n\n' "$range_label" "$(strip_trailer "$(git rev-parse --short "$to_ref")")"
  printf '_Previous tag: %s._\n\n' "$latest_tag_label"
  write_section "Added" "$added_file"
  write_section "Fixed" "$fixed_file"
  write_section "Changed" "$changed_file"
  write_section "Removed" "$removed_file"
} > "$output_file"

echo "Wrote $output_file"
