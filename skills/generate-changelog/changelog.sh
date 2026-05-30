#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"
today="$(date +%Y-%m-%d)"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "${last_tag}" ]]; then
  range="${last_tag}..HEAD"
  heading="Unreleased"
  compare_note="Changes since ${last_tag}"
else
  range="HEAD"
  heading="Initial history"
  compare_note="Changes from the full git history"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

trim() {
  local value="$*"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "${value}"
}

capitalize() {
  local value
  value="$(trim "$*")"
  [[ -z "${value}" ]] && return 0
  printf '%s%s' "$(tr '[:lower:]' '[:upper:]' <<<"${value:0:1}")" "${value:1}"
}

clean_subject() {
  local subject="$1"
  subject="${subject#*:}"
  subject="${subject#*)}"
  subject="${subject# }"
  capitalize "${subject}"
}

append_commit() {
  local hash="$1"
  local subject="$2"
  local normalized
  local item
  normalized="$(tr '[:upper:]' '[:lower:]' <<<"${subject}")"
  item="- $(clean_subject "${subject}") (${hash})"
  case "${normalized}" in
    feat:*|feat\(*|add:*|add\(*|new:*|new\(*|implement:*|implement\(*|create:*|create\(*)
      added+=("${item}") ;;
    fix:*|fix\(*|bug:*|bug\(*|hotfix:*|hotfix\(*|resolve:*|resolve\(*|correct:*|correct\(*)
      fixed+=("${item}") ;;
    remove:*|remove\(*|delete:*|delete\(*|drop:*|drop\(*|deprecate:*|deprecate\(*)
      removed+=("${item}") ;;
    *)
      if [[ "${normalized}" =~ (^|[[:space:]])(remove|delete|drop|deprecat) ]]; then
        removed+=("${item}")
      elif [[ "${normalized}" =~ (^|[[:space:]])(fix|bug|resolve|correct|patch) ]]; then
        fixed+=("${item}")
      elif [[ "${normalized}" =~ (^|[[:space:]])(add|new|introduce|create|implement) ]]; then
        added+=("${item}")
      else
        changed+=("${item}")
      fi ;;
  esac
}

while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash}" || -z "${subject}" ]] && continue
  append_commit "${hash}" "${subject}"
done < <(git log "${range}" --no-merges --pretty=format:'%h%x09%s')

write_section() {
  local title="$1"; shift
  local entries=("$@")
  printf '### %s\n\n' "${title}"
  if (( ${#entries[@]} == 0 )); then
    printf -- '- No changes.\n\n'
  else
    printf '%s\n' "${entries[@]}"
    printf '\n'
  fi
}

tmp_file="$(mktemp)"
previous_file=""
if [[ -f "${output_file}" ]]; then
  previous_file="$(mktemp)"
  awk 'NR==1 && /^# Changelog/{next} NR==2 && /^$/{next} /^All notable/{next} {print}' \
    "${output_file}" >"${previous_file}"
fi

{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project are documented in this file.\n\n'
  printf '## [%s] - %s\n\n' "${heading}" "${today}"
  printf '_%s._\n\n' "${compare_note}"
  write_section "Added"   "${added[@]}"
  write_section "Fixed"   "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
  if [[ -n "${previous_file}" && -s "${previous_file}" ]]; then
    printf '\n'; cat "${previous_file}"
  fi
} >"${tmp_file}"

mv "${tmp_file}" "${output_file}"
[[ -n "${previous_file}" ]] && rm -f "${previous_file}"
echo "Generated ${output_file} from ${compare_note}."
