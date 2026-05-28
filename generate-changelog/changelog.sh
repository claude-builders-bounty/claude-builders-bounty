#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

base_ref="${1:-}"
if [[ -z "$base_ref" ]]; then
  base_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$base_ref" ]]; then
  range="${base_ref}..HEAD"
  since_label="since ${base_ref}"
else
  range="HEAD"
  since_label="from initial commit"
fi

version="${CHANGELOG_VERSION:-Unreleased}"
date_utc="$(date -u +%Y-%m-%d)"
tmp_file="$(mktemp)"

git log --no-merges --reverse --format='%h%x09%s' "$range" > "$tmp_file"

declare -a added fixed changed removed uncategorized
added=()
fixed=()
changed=()
removed=()
uncategorized=()

append_item() {
  local bucket="$1"
  local hash="$2"
  local subject="$3"
  local item="- ${subject} (${hash})"

  case "$bucket" in
    added) added+=("$item") ;;
    fixed) fixed+=("$item") ;;
    changed) changed+=("$item") ;;
    removed) removed+=("$item") ;;
    *) uncategorized+=("$item") ;;
  esac
}

while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue

  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$normalized" in
    feat:*|feat\(*|feature:*|add:*|added:*|implement:*|create:*)
      append_item added "$hash" "$subject"
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|repair:*|resolve:*)
      append_item fixed "$hash" "$subject"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*)
      append_item removed "$hash" "$subject"
      ;;
    refactor:*|change:*|changed:*|update:*|updated:*|improve:*|docs:*|test:*|chore:*|ci:*)
      append_item changed "$hash" "$subject"
      ;;
    *)
      uncategorized+=("- ${subject} (${hash})")
      ;;
  esac
done < "$tmp_file"

rm -f "$tmp_file"

write_section() {
  local title="$1"
  shift
  local items=("$@")

  printf '### %s\n\n' "$title"
  if [[ "${#items[@]}" -eq 0 ]]; then
    printf -- '- No entries.\n\n'
  else
    printf '%s\n' "${items[@]}"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf '## [%s] - %s\n\n' "$version" "$date_utc"
  printf '_Generated from git history %s._\n\n' "$since_label"
  write_section "Added" "${added[@]+"${added[@]}"}"
  write_section "Fixed" "${fixed[@]+"${fixed[@]}"}"
  write_section "Changed" "${changed[@]+"${changed[@]}"}" "${uncategorized[@]+"${uncategorized[@]}"}"
  write_section "Removed" "${removed[@]+"${removed[@]}"}"
} > CHANGELOG.md

echo "Generated CHANGELOG.md (${since_label})"
