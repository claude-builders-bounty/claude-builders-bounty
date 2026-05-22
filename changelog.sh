#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  range_label="since ${last_tag}"
else
  range="HEAD"
  range_label="from initial commit"
fi

repo_url="$(git config --get remote.origin.url || true)"
repo_url="${repo_url%.git}"
if [[ "$repo_url" == git@github.com:* ]]; then
  repo_url="https://github.com/${repo_url#git@github.com:}"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_entry() {
  local category="$1"
  local entry="$2"

  case "$category" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
}

categorize_subject() {
  local subject_lc="$1"

  if [[ "$subject_lc" =~ (^|[[:space:]])(remove|removed|removes|delete|deleted|deletes|drop|dropped|deprecate|deprecated)([[:space:]]|:|\(|$) ]]; then
    echo "Removed"
  elif [[ "$subject_lc" =~ ^(feat|feature)(\(.+\))?!?: ]] || [[ "$subject_lc" =~ (^|[[:space:]])(add|added|adds|create|created|introduce|introduced)([[:space:]]|:|\(|$) ]]; then
    echo "Added"
  elif [[ "$subject_lc" =~ ^fix(\(.+\))?!?: ]] || [[ "$subject_lc" =~ (^|[[:space:]])(fix|fixed|fixes|bugfix|repair|patched|resolve|resolved)([[:space:]]|:|\(|$) ]]; then
    echo "Fixed"
  else
    echo "Changed"
  fi
}

format_entry() {
  local hash="$1"
  local subject="$2"
  local short_hash
  short_hash="$(git rev-parse --short "$hash")"

  if [[ "$repo_url" == https://github.com/* ]]; then
    printf -- "- %s ([%s](%s/commit/%s))" "$subject" "$short_hash" "$repo_url" "$hash"
  else
    printf -- "- %s (%s)" "$subject" "$short_hash"
  fi
}

while IFS=$'\x1f' read -r hash subject body; do
  [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue

  subject_lc="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  body_lc="$(printf '%s' "${body:-}" | tr '[:upper:]' '[:lower:]')"

  if [[ "$subject_lc" == *"breaking change"* || "$body_lc" == *"breaking change"* || "$subject_lc" =~ ^.+!: ]]; then
    category="Changed"
  else
    category="$(categorize_subject "$subject_lc")"
  fi

  append_entry "$category" "$(format_entry "$hash" "$subject")"
done < <(git log "$range" --no-merges --pretty=format:'%H%x1f%s%x1f%b')

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title"
  if (( ${#entries[@]} == 0 )); then
    printf -- "- No changes.\n\n"
    return
  fi

  printf '%s\n' "${entries[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated on %s for commits %s.\n\n' "$(date -u +%Y-%m-%d)" "$range_label"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$OUTPUT_FILE"

echo "Wrote ${OUTPUT_FILE}"
