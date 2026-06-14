#!/usr/bin/env bash
set -euo pipefail

output="CHANGELOG.md"
since_ref=""
dry_run="false"

usage() {
  cat <<'USAGE'
Usage: bash scripts/changelog.sh [--since <tag-or-ref>] [--output <file>] [--dry-run]

Generates a structured CHANGELOG.md from commits since the latest git tag.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --since)
      since_ref="${2:-}"
      shift 2
      ;;
    --output)
      output="${2:-}"
      shift 2
      ;;
    --dry-run)
      dry_run="true"
      shift
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

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository." >&2
  exit 1
fi

if [ -z "$since_ref" ]; then
  if since_ref="$(git describe --tags --abbrev=0 2>/dev/null)"; then
    range="${since_ref}..HEAD"
  else
    range="HEAD"
    since_ref="the first commit"
  fi
else
  range="${since_ref}..HEAD"
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "No commits found." >&2
  exit 1
fi

today="$(date +%Y-%m-%d)"
version="Unreleased"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added="$tmp_dir/added"
fixed="$tmp_dir/fixed"
changed="$tmp_dir/changed"
removed="$tmp_dir/removed"
: >"$added"
: >"$fixed"
: >"$changed"
: >"$removed"

append_commit() {
  subject="$1"
  hash="$2"
  short_hash="$(printf '%s' "$hash" | cut -c1-7)"
  clean_subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
  item="- ${clean_subject} (${short_hash})"

  lower_subject="$(printf '%s' "$clean_subject" | tr '[:upper:]' '[:lower:]')"
  case "$lower_subject" in
    feat:*|feature:*|add:*|added:*|*add\ *|*new\ *)
      printf '%s\n' "$item" >>"$added"
      ;;
    fix:*|bug:*|bugfix:*|patch:*|*fix\ *|*bug\ *)
      printf '%s\n' "$item" >>"$fixed"
      ;;
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|*remove\ *|*delete\ *)
      printf '%s\n' "$item" >>"$removed"
      ;;
    *)
      printf '%s\n' "$item" >>"$changed"
      ;;
  esac
}

while IFS=$'\t' read -r hash subject || [ -n "${hash:-}" ]; do
  [ -n "${hash:-}" ] || continue
  [ -n "${subject:-}" ] || continue
  case "$subject" in
    Merge\ *) continue ;;
  esac
  append_commit "$subject" "$hash"
done < <(git log "$range" --no-decorate --pretty=format:'%H%x09%s')

section() {
  title="$1"
  file="$2"
  if [ -s "$file" ]; then
    printf '### %s\n\n' "$title"
    cat "$file"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf '## [%s] - %s\n\n' "$version" "$today"
  section "Added" "$added"
  section "Fixed" "$fixed"
  section "Changed" "$changed"
  section "Removed" "$removed"
} >"$tmp_dir/changelog"

if ! grep -q '^- ' "$tmp_dir/changelog"; then
  printf '# Changelog\n\n## [%s] - %s\n\nNo user-facing changes since %s.\n' "$version" "$today" "$since_ref" >"$tmp_dir/changelog"
fi

if [ "$dry_run" = "true" ]; then
  cat "$tmp_dir/changelog"
else
  cp "$tmp_dir/changelog" "$output"
  echo "Wrote $output from commits since $since_ref."
fi

