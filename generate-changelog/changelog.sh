#!/usr/bin/env bash
set -euo pipefail

output="CHANGELOG.md"
since_ref=""

usage() {
  printf 'Usage: %s [--since <git-ref>] [--output <path>]\n' "$0"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --since)
      [ "$#" -ge 2 ] || { usage >&2; exit 2; }
      since_ref="$2"
      shift 2
      ;;
    --output)
      [ "$#" -ge 2 ] || { usage >&2; exit 2; }
      output="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null

if [ -z "$since_ref" ]; then
  since_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [ -n "$since_ref" ]; then
  range="${since_ref}..HEAD"
  range_label="since ${since_ref}"
else
  range="HEAD"
  range_label="from initial commit"
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

added="$tmpdir/added"
fixed="$tmpdir/fixed"
changed="$tmpdir/changed"
removed="$tmpdir/removed"
touch "$added" "$fixed" "$changed" "$removed"

categorize() {
  subject="$1"
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    feat:*|feat\(*|add:*|add\ *|added:*|new:*|*\ add\ *|*\ adds\ *)
      printf '%s\n' "$added"
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|*\ fix\ *|*\ fixes\ *|*\ fixed\ *)
      printf '%s\n' "$fixed"
      ;;
    remove:*|remove\ *|removed:*|delete:*|delete\ *|deleted:*|drop:*|drop\ *|dropped:*|*\ remove\ *|*\ delete\ *)
      printf '%s\n' "$removed"
      ;;
    *)
      printf '%s\n' "$changed"
      ;;
  esac
}

while IFS='|' read -r sha subject; do
  [ -n "$sha" ] || continue
  bucket="$(categorize "$subject")"
  printf -- '- %s (`%s`)\n' "$subject" "$sha" >> "$bucket"
done <<EOF_COMMITS
$(git log "$range" --no-merges --date-order --pretty=format:'%h|%s')
EOF_COMMITS

today="$(date +%Y-%m-%d)"
{
  printf '# Changelog\n\n'
  printf 'All notable changes generated from git history %s.\n\n' "$range_label"
  printf '## Unreleased - %s\n\n' "$today"
  for pair in "Added:$added" "Fixed:$fixed" "Changed:$changed" "Removed:$removed"; do
    heading="${pair%%:*}"
    file="${pair#*:}"
    printf '### %s\n\n' "$heading"
    if [ -s "$file" ]; then
      cat "$file"
    else
      printf -- '- No changes.\n'
    fi
    printf '\n'
  done
} > "$output"

printf 'Wrote %s (%s)\n' "$output" "$range_label"
