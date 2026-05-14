#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$last_tag" ]; then
  range="$last_tag..HEAD"
  heading="Unreleased"
else
  range="HEAD"
  heading="Initial history"
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

git log "$range" --reverse --pretty=format:'%s%x09%h' > "$tmp"

declare -a added fixed changed removed

clean_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#*:}"
  subject="${subject#*) }"
  subject="${subject#*)}"
  printf '%s' "$subject"
}

while IFS=$'\t' read -r subject hash || [ -n "${subject:-}" ]; do
  [ -n "${subject:-}" ] || continue
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  line="$(clean_subject "$subject") ($hash)"

  case "$lower" in
    feat:*|feat\(*|feature:*|add:*|added:*|create:*|new:*)
      added+=("$line")
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|repair:*)
      fixed+=("$line")
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*|deprecated:*)
      removed+=("$line")
      ;;
    refactor:*|refactor\(*|change:*|changed:*|update:*|updated:*|improve:*|improved:*|perf:*|docs:*|chore:*)
      changed+=("$line")
      ;;
    *)
      changed+=("$line")
      ;;
  esac
done < "$tmp"

write_section() {
  local title="$1"
  shift
  local items=("$@")
  [ "${#items[@]}" -gt 0 ] || return 0

  {
    echo
    echo "### $title"
    for item in "${items[@]}"; do
      echo "- $item"
    done
  } >> "$OUT"
}

{
  echo "# Changelog"
  echo
  echo "## [$heading] - $(date +%Y-%m-%d)"
} > "$OUT"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

echo "Wrote $OUT"
