#!/usr/bin/env bash
set -euo pipefail
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo 'Run inside a Git repository' >&2; exit 1
fi
last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
else
  range="HEAD"
fi
out=${1:-CHANGELOG.md}
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
printf '# Changelog\n\nChanges since %s\n\n' "${last_tag:-repository start}" > "$tmp"
for category in Added Fixed Changed Removed; do
  printf '## %s\n\n' "$category" >> "$tmp"
  count=0
  while IFS=$'\t' read -r sha subject; do
    [[ -n "$sha" ]] || continue
    type=${subject%%:*}
    case "$type" in
      feat|feat\(*) target=Added;;
      fix|fix\(*) target=Fixed;;
      remove|removed|revert|delete|drop) target=Removed;;
      *) target=Changed;;
    esac
    if [[ "$category" == "$target" ]]; then
      printf -- '- %s (`%s`)\n' "$subject" "${sha:0:7}" >> "$tmp"
      count=$((count+1))
    fi
  done < <(git log "$range" --no-merges --format='%H%x09%s')
  if ((count == 0)); then printf -- '- No changes.\n' >> "$tmp"; fi
  printf '\n' >> "$tmp"
done
mv "$tmp" "$out"
trap - EXIT
printf 'Wrote %s\n' "$out"
