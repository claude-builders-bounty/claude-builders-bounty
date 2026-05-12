#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
REMOTE_NAME="${CHANGELOG_REMOTE:-origin}"

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash scripts/changelog.sh [--stdout] [--output PATH] [--no-fetch]

Options:
  --stdout       Print the changelog instead of writing CHANGELOG.md.
  --output PATH  Write to PATH instead of CHANGELOG.md.
  --no-fetch     Skip fetching tags from the configured remote.
USAGE
}

WRITE_STDOUT=0
FETCH_TAGS=1

while [ "$#" -gt 0 ]; do
  case "$1" in
    --stdout)
      WRITE_STDOUT=1
      shift
      ;;
    --output)
      if [ "$#" -lt 2 ]; then
        echo "Missing value for --output" >&2
        exit 2
      fi
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --no-fetch)
      FETCH_TAGS=0
      shift
      ;;
    -h|--help)
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

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This script must be run inside a git repository." >&2
  exit 1
fi

if [ "$FETCH_TAGS" -eq 1 ] && git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  git fetch --tags "$REMOTE_NAME" --quiet || true
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$latest_tag" ]; then
  range="${latest_tag}..HEAD"
  base_label="$latest_tag"
else
  range="HEAD"
  base_label="initial commit"
fi

if ! git rev-list --max-count=1 "$range" >/dev/null 2>&1; then
  echo "No commits found for range $range." >&2
  exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

touch "$tmp_dir/Added" "$tmp_dir/Fixed" "$tmp_dir/Changed" "$tmp_dir/Removed"

categorize() {
  subject_lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject_lc" in
    feat:*|feat\(*|feature:*|add:*|added:*|create:*|created:*|implement:*|implemented:*|introduce:*|introduced:*)
      printf 'Added'
      ;;
    fix:*|fix\(*|fixed:*|bug:*|bugfix:*|patch:*|repair:*|resolve:*|resolved:*)
      printf 'Fixed'
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*)
      printf 'Removed'
      ;;
    refactor:*|refactor\(*|change:*|changed:*|update:*|updated:*|chore:*|docs:*|doc:*|test:*|tests:*|perf:*|style:*|ci:*|build:*)
      printf 'Changed'
      ;;
    *)
      if printf '%s' "$subject_lc" | grep -Eq '(^|[[:space:]])(remove|delete|drop|deprecat)[a-z]*([[:space:]]|$)'; then
        printf 'Removed'
      elif printf '%s' "$subject_lc" | grep -Eq '(^|[[:space:]])(fix|bug|patch|repair|resolve)[a-z]*([[:space:]]|$)'; then
        printf 'Fixed'
      elif printf '%s' "$subject_lc" | grep -Eq '(^|[[:space:]])(add|create|implement|introduce)[a-z]*([[:space:]]|$)'; then
        printf 'Added'
      else
        printf 'Changed'
      fi
      ;;
  esac
}

git log "$range" --no-merges --reverse --pretty=format:'%h%x09%s' |
while IFS="$(printf '\t')" read -r hash subject || [ -n "${hash:-}" ]; do
  [ -n "${hash:-}" ] || continue
  category="$(categorize "$subject")"
  printf -- '- %s (`%s`)\n' "$subject" "$hash" >> "$tmp_dir/$category"
done

today="${CHANGELOG_DATE:-$(date +%Y-%m-%d)}"
repo_name="$(basename "$(git rev-parse --show-toplevel)")"

{
  printf '# Changelog\n\n'
  printf 'All notable changes generated from git history for `%s`.\n\n' "$repo_name"
  printf '## Unreleased - %s\n\n' "$today"
  printf '_Commits since %s._\n\n' "$base_label"

  for category in Added Fixed Changed Removed; do
    if [ -s "$tmp_dir/$category" ]; then
      printf '### %s\n\n' "$category"
      cat "$tmp_dir/$category"
      printf '\n'
    fi
  done
} > "$tmp_dir/changelog"

if [ "$WRITE_STDOUT" -eq 1 ]; then
  cat "$tmp_dir/changelog"
else
  cp "$tmp_dir/changelog" "$OUTPUT_FILE"
  printf 'Wrote %s from commits since %s\n' "$OUTPUT_FILE" "$base_label"
fi
