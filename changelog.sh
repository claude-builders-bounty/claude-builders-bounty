#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
if [ "$#" -gt 0 ]; then
  output_file="$1"
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

if latest_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range="$latest_tag..HEAD"
  heading="Changes since $latest_tag"
else
  range="HEAD"
  heading="All changes"
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
today="$(date +%Y-%m-%d)"
tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

{
  echo "# Changelog"
  echo
  echo "Generated for $repo_name on $today."
  echo
  echo "## $heading"
  echo
} >"$tmp_file"

commit_count="$(git rev-list --count "$range" 2>/dev/null || echo 0)"
if [ "$commit_count" = "0" ]; then
  echo "- No commits found for this range." >>"$tmp_file"
else
  git log "$range" --date=short --pretty=format:'%H%x1f%h%x1f%ad%x1f%s%x1f%an' |
  while IFS=$'\x1f' read -r full_hash short_hash commit_date subject author || [ -n "$full_hash" ]; do
    type="Other"
    case "$subject" in
      feat:*|feat\(*) type="Features" ;;
      fix:*|fix\(*) type="Fixes" ;;
      docs:*|docs\(*) type="Documentation" ;;
      test:*|tests:*|test\(*|tests\(*) type="Tests" ;;
      chore:*|build:*|ci:*|refactor:*|perf:*|style:*|chore\(*|build\(*|ci\(*|refactor\(*|perf\(*|style\(*) type="Maintenance" ;;
    esac
    printf '%s\t- %s (%s, %s, %s)\n' "$type" "$subject" "$short_hash" "$commit_date" "$author"
  done |
  awk -F '\t' '
    { entries[$1]=entries[$1] $2 "\n" }
    END {
      split("Features Fixes Documentation Tests Maintenance Other", preferred, " ")
      for (i=1; i<=length(preferred); i++) {
        bucket=preferred[i]
        if (entries[bucket] != "") {
          print "### " bucket
          printf "%s\n", entries[bucket]
        }
      }
    }
  ' >>"$tmp_file"
fi

mv "$tmp_file" "$output_file"
trap - EXIT
echo "Wrote $output_file"
