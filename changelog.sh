#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag=""
if latest_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  range="HEAD"
  range_label="from repository history"
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "error: repository has no commits" >&2
  exit 1
fi

commit_lines=$(git log --reverse --pretty=format:'%s%x09%h' "$range")
release_date=$(date -u +%Y-%m-%d)

category_for_subject() {
  subject="$1"
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    feat:*|feature:*|add:*|added:*|new:*|*" add "*|*" adds "*) printf 'Added' ;;
    fix:*|bugfix:*|bug:*|*" fix "*|*" fixes "*|*" fixed "*) printf 'Fixed' ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|*" remove "*|*" delete "*) printf 'Removed' ;;
    change:*|changed:*|update:*|updated:*|refactor:*|perf:*|docs:*|test:*|chore:*) printf 'Changed' ;;
    *) printf 'Changed' ;;
  esac
}

print_section() {
  title="$1"
  entries="$2"
  printf '\n## %s\n\n' "$title"
  if [ -n "$entries" ]; then
    printf '%s\n' "$entries"
  else
    printf -- '- No changes.\n'
  fi
}

added=""
fixed=""
changed=""
removed=""

while IFS=$'\t' read -r subject short_hash; do
  [ -n "${subject:-}" ] || continue
  entry="- ${subject} (${short_hash})"
  category=$(category_for_subject "$subject")
  case "$category" in
    Added) added="${added}${entry}\n" ;;
    Fixed) fixed="${fixed}${entry}\n" ;;
    Removed) removed="${removed}${entry}\n" ;;
    *) changed="${changed}${entry}\n" ;;
  esac
done <<EOF_COMMITS
${commit_lines}
EOF_COMMITS

strip_trailing_newline() {
  printf '%b' "$1" | sed '/^$/d'
}

{
  printf '# Changelog\n\n'
  printf 'Generated on %s (%s).\n' "$release_date" "$range_label"
  print_section 'Added' "$(strip_trailing_newline "$added")"
  print_section 'Fixed' "$(strip_trailing_newline "$fixed")"
  print_section 'Changed' "$(strip_trailing_newline "$changed")"
  print_section 'Removed' "$(strip_trailing_newline "$removed")"
} > "$output_file"

printf 'Wrote %s using commits %s\n' "$output_file" "$range_label"
