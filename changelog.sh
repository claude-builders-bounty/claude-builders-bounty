#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$latest_tag" ]; then
  range="$latest_tag..HEAD"
  since_label="since $latest_tag"
else
  range="HEAD"
  since_label="from the full git history"
fi

mapfile -t commits < <(git log --no-merges --pretty=format:'%s|%h' "$range")

categorize() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*) echo "Added" ;;
    fix:*|bug:*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" bug "*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|*" remove "*|*" removes "*) echo "Removed" ;;
    refactor:*|change:*|changed:*|update:*|updated:*|docs:*|chore:*|style:*|test:*|ci:*) echo "Changed" ;;
    *) echo "Changed" ;;
  esac
}

sanitize_subject() {
  printf '%s' "$1" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//'
}

declare -a added=() fixed=() changed=() removed=()

for entry in "${commits[@]}"; do
  subject="${entry%|*}"
  hash="${entry##*|}"
  line="$(sanitize_subject "$subject") ($hash)"
  case "$(categorize "$subject")" in
    Added) added+=("$line") ;;
    Fixed) fixed+=("$line") ;;
    Removed) removed+=("$line") ;;
    *) changed+=("$line") ;;
  esac
done

write_section() {
  local title="$1"
  shift
  local items=("$@")
  printf '### %s\n\n' "$title"
  if [ "${#items[@]}" -eq 0 ]; then
    printf -- '- No changes.\n\n'
    return
  fi
  for item in "${items[@]}"; do
    printf -- '- %s\n' "$item"
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated %s.\n\n' "$since_label"
  printf '## Unreleased\n\n'
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$output_file"

echo "Wrote $output_file"
