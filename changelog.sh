#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  range="HEAD"
  range_label="from all commits"
fi

added=""
fixed=""
changed=""
removed=""

clean_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#*): }"
  printf '%s' "$subject"
}

add_commit() {
  local subject="$1"
  local normalized
  local cleaned
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  cleaned="$(clean_subject "$subject")"

  case "$normalized" in
    feat:*|feat\(*|add:*|added:*|new:*|implement:*|create:*)
      added="${added}- ${cleaned}"$'\n'
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|repair:*)
      fixed="${fixed}- ${cleaned}"$'\n'
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*)
      removed="${removed}- ${cleaned}"$'\n'
      ;;
    chore:*|refactor:*|perf:*|style:*|test:*|docs:*|ci:*|build:*|change:*|changed:*|update:*|updated:*)
      changed="${changed}- ${cleaned}"$'\n'
      ;;
    *)
      changed="${changed}- ${subject}"$'\n'
      ;;
  esac
}

write_section() {
  local title="$1"
  local items="$2"

  printf '### %s\n\n' "$title"
  if [[ -z "$items" ]]; then
    printf -- '- None\n\n'
    return
  fi

  printf '%s\n' "$items"
}

while IFS= read -r commit; do
  [[ -n "$commit" ]] || continue
  add_commit "$commit"
done < <(git log --no-merges --reverse --format='%s' "$range")

{
  printf '# Changelog\n\n'
  printf 'Generated %s for commits %s.\n\n' "$(date -u +%Y-%m-%d)" "$range_label"
  write_section "Added" "$added"
  write_section "Fixed" "$fixed"
  write_section "Changed" "$changed"
  write_section "Removed" "$removed"
} > "$output_file"

echo "Wrote ${output_file}"
