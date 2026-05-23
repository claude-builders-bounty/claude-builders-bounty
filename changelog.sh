#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--repo PATH] [--output PATH]

Generate a structured CHANGELOG.md from git commits since the last tag.

Options:
  --repo PATH     Git repository to inspect. Defaults to the current directory.
  --output PATH   File to write. Defaults to CHANGELOG.md in the repo.
  -h, --help      Show this help text.
USAGE
}

repo="."
output=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      if [ -z "$repo" ]; then
        echo "error: --repo requires a path" >&2
        exit 1
      fi
      shift 2
      ;;
    --output)
      output="${2:-}"
      if [ -z "$output" ]; then
        echo "error: --output requires a path" >&2
        exit 1
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: $repo is not a git repository" >&2
  exit 1
fi

if [ -z "$output" ]; then
  output="$repo/CHANGELOG.md"
fi

last_tag="$(git -C "$repo" describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$last_tag" ]; then
  range="$last_tag..HEAD"
  source_label="since $last_tag"
else
  range="HEAD"
  source_label="from all commits because no git tag was found"
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

categorize_commit() {
  subject="$1"
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|add:*|add\(*|added:*|added\(*)
      printf '%s\n' "Added"
      ;;
    fix:*|fix\(*|fixed:*|fixed\(*|bug:*|bugfix:*|patch:*)
      printf '%s\n' "Fixed"
      ;;
    remove:*|remove\(*|removed:*|removed\(*|delete:*|delete\(*|deleted:*|drop:*|drop\(*|deprecate:*|deprecate\(*)
      printf '%s\n' "Removed"
      ;;
    *)
      printf '%s\n' "Changed"
      ;;
  esac
}

append_commit() {
  category="$1"
  subject="$2"
  hash="$3"
  line="- ${subject} (${hash})"

  case "$category" in
    Added) printf '%s\n' "$line" >> "$added" ;;
    Fixed) printf '%s\n' "$line" >> "$fixed" ;;
    Removed) printf '%s\n' "$line" >> "$removed" ;;
    *) printf '%s\n' "$line" >> "$changed" ;;
  esac
}

while IFS=$'\t' read -r subject hash || [ -n "${subject:-}" ]; do
  [ -n "$subject" ] || continue
  category="$(categorize_commit "$subject")"
  append_commit "$category" "$subject" "$hash"
done < <(git -C "$repo" log "$range" --no-merges --pretty=format:'%s%x09%h')

write_section() {
  title="$1"
  file="$2"

  if [ -s "$file" ]; then
    {
      printf '### %s\n\n' "$title"
      cat "$file"
      printf '\n\n'
    } >> "$output"
  fi
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$(date +%Y-%m-%d)"
  printf 'Generated from git history %s.\n\n' "$source_label"
} > "$output"

write_section "Added" "$added"
write_section "Fixed" "$fixed"
write_section "Changed" "$changed"
write_section "Removed" "$removed"

if ! grep -q '^- ' "$output"; then
  {
    printf '### Changed\n\n'
    printf -- '- No commits found for this range.\n'
  } >> "$output"
fi

printf 'Wrote %s\n' "$output"
