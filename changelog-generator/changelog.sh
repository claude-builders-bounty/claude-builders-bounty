#!/usr/bin/env bash
set -euo pipefail

output="CHANGELOG.md"
if [[ "${1:-}" == "--output" ]]; then
  output="${2:?missing output path}"
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
range="${last_tag:+${last_tag}..}HEAD"

declare -A sections=(
  [Added]="add|new|introduc|create|support"
  [Fixed]="fix|bug|patch|repair|correct"
  [Changed]="change|update|improve|refactor|rename|move"
  [Removed]="remove|delete|drop|deprecate"
)

declare -A entries
for section in Added Fixed Changed Removed; do entries[$section]=""; done

while IFS=$'\t' read -r hash subject; do
  [[ -z "$hash" ]] && continue
  lower="${subject,,}"
  section=Changed
  for candidate in Added Fixed Removed Changed; do
    if [[ "$lower" =~ (${sections[$candidate]}) ]]; then
      section="$candidate"
      break
    fi
  done
  entries[$section]+="- ${subject} ([${hash:0:7}])"$'\n'
done < <(git log --format='%h%x09%s' "$range" --no-merges)

{
  echo "# Changelog"
  echo
  echo "Generated from git history $(date -u +%Y-%m-%d)."
  echo
  for section in Added Fixed Changed Removed; do
    if [[ -n "${entries[$section]}" ]]; then
      echo "## $section"
      printf '%s' "${entries[$section]}"
      echo
    fi
  done
} > "$output"

echo "Wrote $output"
