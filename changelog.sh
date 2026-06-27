#!/usr/bin/env bash
set -euo pipefail

out=${1:-CHANGELOG.md}

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: run this from inside a git repository" >&2
  exit 1
fi

last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [[ -n "$last_tag" ]]; then
  range="$last_tag..HEAD"
  scope="since $last_tag"
else
  range="HEAD"
  scope="from the first commit"
fi

added=()
fixed=()
changed=()
removed=()

while IFS=$'\x1f' read -r subject hash; do
  [[ -z "${subject}${hash}" ]] && continue
  line="- ${subject} (\`${hash}\`)"
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')

  case "$lower" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" added "*) added+=("$line") ;;
    fix:*|fixed:*|bug:*|*" fix "*|*" fixed "*) fixed+=("$line") ;;
    remove:*|removed:*|delete:*|deleted:*|*" remove "*|*" removed "*) removed+=("$line") ;;
    change:*|changed:*|refactor:*|perf:*|chore:*|docs:*|test:*|ci:*) changed+=("$line") ;;
    *) changed+=("$line") ;;
  esac
done < <(git log --reverse --format='%s%x1f%h' "$range")

write_section() {
  local title=$1
  shift
  local items=("$@")

  printf '## %s\n\n' "$title"
  if (( ${#items[@]} == 0 )); then
    printf -- '- No changes.\n\n'
    return
  fi

  printf '%s\n' "${items[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated on %s for commits %s.\n\n' "$(date +%Y-%m-%d)" "$scope"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$out"

printf 'Wrote %s\n' "$out"
