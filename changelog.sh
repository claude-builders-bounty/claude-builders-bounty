#!/usr/bin/env bash
set -euo pipefail

out="${1:-CHANGELOG.md}"
latest_tag=""
range=""

if latest_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range="${latest_tag}..HEAD"
else
  latest_tag="initial history"
  range="HEAD"
fi

commit_lines="$(git log --no-merges --pretty=format:'%s' "$range")"

category_for() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    fix:*|fix\(*|fixed:*|bug:*|bugfix:*|hotfix:*|*fix*|*bug*) printf 'Fixed' ;;
    add:*|added:*|feat:*|feature:*|new:*|*add*|*implement*) printf 'Added' ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|*remove*|*delete*) printf 'Removed' ;;
    change:*|changed:*|chore:*|refactor:*|update:*|docs:*|style:*|perf:*|test:*|*change*|*update*|*refactor*) printf 'Changed' ;;
    *) printf 'Changed' ;;
  esac
}

section_file() {
  printf '%s/%s' "$tmpdir" "$1"
}

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
for section in Added Fixed Changed Removed; do : > "$(section_file "$section")"; done

if [ -n "$commit_lines" ]; then
  while IFS= read -r subject; do
    [ -z "$subject" ] && continue
    category="$(category_for "$subject")"
    printf -- '- %s\n' "$subject" >> "$(section_file "$category")"
  done <<EOF_COMMITS
$commit_lines
EOF_COMMITS
fi

{
  printf '# Changelog\n\n'
  printf 'Generated from commits since `%s`.\n\n' "$latest_tag"
  printf '## Unreleased\n\n'
  for section in Added Fixed Changed Removed; do
    printf '### %s\n' "$section"
    if [ -s "$(section_file "$section")" ]; then
      cat "$(section_file "$section")"
    else
      printf -- '- No changes.\n'
    fi
    printf '\n'
  done
} > "$out"

printf 'Wrote %s using commits since %s\n' "$out" "$latest_tag"
