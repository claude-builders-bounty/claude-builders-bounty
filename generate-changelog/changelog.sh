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
  range_label="for all commits"
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
generated_at="$(date -u +"%Y-%m-%d")"
commit_log="$(git log "$range" --no-merges --pretty=format:'%H%x1f%s%x1e' || true)"

declare -a added fixed changed removed

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

sentence_case() {
  local value
  value="$(trim "$1")"
  value="${value#*: }"
  value="${value#*:}"
  value="${value#- }"
  value="$(trim "$value")"
  [[ -z "$value" ]] && return
  printf '%s%s' "$(tr '[:lower:]' '[:upper:]' <<<"${value:0:1}")" "${value:1}"
}

append_entry() {
  local category="$1"
  local subject="$2"
  local hash="$3"
  local entry
  entry="$(sentence_case "$subject")"
  [[ -z "$entry" ]] && return
  entry="- ${entry} (${hash:0:7})"

  case "$category" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    changed) changed+=("$entry") ;;
    removed) removed+=("$entry") ;;
  esac
}

categorize_subject() {
  local subject_lower="$1"

  if [[ "$subject_lower" =~ ^(feat|feature|add)(\(.+\))?!?: ]] ||
     [[ "$subject_lower" =~ (^|[[:space:]])(add|adds|added|new|introduce|introduces|create|creates|implement|implements)([[:space:]]|$) ]]; then
    printf 'added'
  elif [[ "$subject_lower" =~ ^(fix|bugfix|hotfix)(\(.+\))?!?: ]] ||
       [[ "$subject_lower" =~ (^|[[:space:]])(fix|fixes|fixed|bug|repair|patch|resolve|resolves|resolved)([[:space:]]|$) ]]; then
    printf 'fixed'
  elif [[ "$subject_lower" =~ ^(remove|delete|drop)(\(.+\))?!?: ]] ||
       [[ "$subject_lower" =~ (^|[[:space:]])(remove|removes|removed|delete|deletes|deleted|drop|drops|dropped|deprecate|deprecates)([[:space:]]|$) ]]; then
    printf 'removed'
  else
    printf 'changed'
  fi
}

if [[ -n "$commit_log" ]]; then
  while IFS=$'\x1f' read -r hash subject; do
    [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue
    subject_lower="$(tr '[:upper:]' '[:lower:]' <<<"$subject")"
    category="$(categorize_subject "$subject_lower")"
    append_entry "$category" "$subject" "$hash"
  done < <(printf '%s' "$commit_log" | tr '\036' '\n')
fi

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n' "$title"
  if (( ${#entries[@]} == 0 )); then
    printf -- '- Nothing notable.\n\n'
    return
  fi

  printf '%s\n' "${entries[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated for `%s` %s on %s.\n\n' "$repo_name" "$range_label" "$generated_at"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$OUTPUT_FILE"

echo "Wrote ${OUTPUT_FILE}"
