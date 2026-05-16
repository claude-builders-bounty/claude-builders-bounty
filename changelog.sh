#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
current_date="$(date +%Y-%m-%d)"

last_tag=""
if last_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range="${last_tag}..HEAD"
  since_label="since ${last_tag}"
else
  range="HEAD"
  since_label="for all commits"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()
commit_count=0

clean_subject() {
  local subject="$1"
  subject="$(printf '%s' "${subject}" | sed -E 's/^(feat|fix|change|changed|chore|docs|refactor|remove|removed|delete|deleted)(\([^)]*\))?:[[:space:]]*//I')"
  subject="$(printf '%s' "${subject}" | sed -E 's/^BREAKING CHANGE:[[:space:]]*//I')"
  printf '%s' "${subject}"
}

add_entry() {
  local bucket="$1"
  local subject="$2"
  local hash="$3"
  local line="- $(clean_subject "${subject}") (${hash})"

  case "${bucket}" in
    added) added+=("${line}") ;;
    fixed) fixed+=("${line}") ;;
    removed) removed+=("${line}") ;;
    *) changed+=("${line}") ;;
  esac
}

while IFS= read -r row || [ -n "${row}" ]; do
  [ -n "${row}" ] || continue
  commit_count=$((commit_count + 1))
  subject="${row%%$'\t'*}"
  hash="${row##*$'\t'}"
  lower="$(printf '%s' "${subject}" | tr '[:upper:]' '[:lower:]')"

  case "${lower}" in
    feat:*|feat\(*|add:*|added:*|create:*|new:*)
      add_entry added "${subject}" "${hash}"
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*)
      add_entry fixed "${subject}" "${hash}"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*)
      add_entry removed "${subject}" "${hash}"
      ;;
    *)
      add_entry changed "${subject}" "${hash}"
      ;;
  esac
done < <(git log "${range}" --pretty=format:'%s%x09%h' --no-merges)

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  {
    if [ "${section_started}" -eq 1 ]; then
      printf '\n'
    fi
    section_started=1
    printf '### %s\n\n' "${title}"
    if ((${#entries[@]} == 0)); then
      printf -- '- No changes.\n'
    else
      printf '%s\n' "${entries[@]}"
    fi
  } >> "${output_file}"
}

{
  printf '# Changelog\n\n'
  printf 'Generated on %s for `%s` from commits %s.\n\n' "${current_date}" "${repo_name}" "${since_label}"
} > "${output_file}"

section_started=0
write_section "Added" "${added[@]+"${added[@]}"}"
write_section "Fixed" "${fixed[@]+"${fixed[@]}"}"
write_section "Changed" "${changed[@]+"${changed[@]}"}"
write_section "Removed" "${removed[@]+"${removed[@]}"}"

echo "Wrote ${output_file} using ${commit_count} commit(s) ${since_label}."
