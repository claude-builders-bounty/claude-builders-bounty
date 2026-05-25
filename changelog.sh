#!/usr/bin/env bash
set -euo pipefail

out="${1:-CHANGELOG.md}"
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "${last_tag}" ]]; then
  range="${last_tag}..HEAD"
  since="${last_tag}"
else
  range="HEAD"
  since="initial commit"
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

git log --no-merges --format='%s' ${range} > "$tmp"

add_lines=()
fix_lines=()
chg_lines=()
rem_lines=()
other_lines=()

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  clean="$subject"
  clean="${clean#feat: }"; clean="${clean#feat(}"
  case "$subject" in
    feat:*|*"[feat]"*|*"[feature]"*) add_lines+=("- ${subject}") ;;
    fix:*|bug:*|*"[fix]"*|*"bug"*) fix_lines+=("- ${subject}") ;;
    refactor:*|docs:*|chore:*|style:*|test:*|perf:*) chg_lines+=("- ${subject}") ;;
    remove:*|revert:*|*"[remove]"*) rem_lines+=("- ${subject}") ;;
    *) other_lines+=("- ${subject}") ;;
  esac
done < "$tmp"

{
  echo "# Changelog"
  echo
  echo "Generated from git history since ${since}."
  echo
  printf '## Added\n'
  ((${#add_lines[@]})) && printf '%s\n' "${add_lines[@]}" || echo "- None"
  echo
  printf '## Fixed\n'
  ((${#fix_lines[@]})) && printf '%s\n' "${fix_lines[@]}" || echo "- None"
  echo
  printf '## Changed\n'
  ((${#chg_lines[@]})) && printf '%s\n' "${chg_lines[@]}" || echo "- None"
  echo
  printf '## Removed\n'
  ((${#rem_lines[@]})) && printf '%s\n' "${rem_lines[@]}" || echo "- None"
  if ((${#other_lines[@]})); then
    echo
    printf '## Other\n'
    printf '%s\n' "${other_lines[@]}"
  fi
} > "$out"

echo "Wrote $out"
