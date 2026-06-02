#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

output_path="${1:-CHANGELOG.md}"
latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "${latest_tag}" ]]; then
  range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  range="HEAD"
  range_label="from repository history"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_commit() {
  local bucket="$1"
  local entry="$2"

  case "${bucket}" in
    added) added+=("${entry}") ;;
    fixed) fixed+=("${entry}") ;;
    changed) changed+=("${entry}") ;;
    removed) removed+=("${entry}") ;;
  esac
}

categorize_subject() {
  local subject_lower="$1"

  case "${subject_lower}" in
    feat:*|feat\(*|add:*|add\ *|create:*|create\ *|implement:*|implement\ *)
      echo "added"
      ;;
    fix:*|fix\(*|bug:*|bug\ *|patch:*|patch\ *|repair:*|repair\ *)
      echo "fixed"
      ;;
    remove:*|remove\ *|delete:*|delete\ *|drop:*|drop\ *)
      echo "removed"
      ;;
    *)
      echo "changed"
      ;;
  esac
}

while IFS= read -r commit; do
  [[ -n "${commit}" ]] || continue
  sha="${commit%%$'\t'*}"
  subject="${commit#*$'\t'}"
  subject_lower="$(printf '%s' "${subject}" | tr '[:upper:]' '[:lower:]')"
  bucket="$(categorize_subject "${subject_lower}")"
  append_commit "${bucket}" "- ${subject} (${sha})"
done < <(git log --reverse --pretty=format:'%h%x09%s' "${range}")

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  {
    printf '### %s\n\n' "${title}"
    if [[ "${#entries[@]}" -eq 0 ]]; then
      printf -- '- No changes.\n\n'
    else
      printf '%s\n' "${entries[@]}"
      printf '\n'
    fi
  } >> "${output_path}"
}

generated_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

{
  printf '# Changelog\n\n'
  printf 'Generated at `%s` from commits %s.\n\n' "${generated_at}" "${range_label}"
  printf '## Unreleased\n\n'
} > "${output_path}"

write_section "Added" "${added[@]+"${added[@]}"}"
write_section "Fixed" "${fixed[@]+"${fixed[@]}"}"
write_section "Changed" "${changed[@]+"${changed[@]}"}"
write_section "Removed" "${removed[@]+"${removed[@]}"}"

echo "Wrote ${output_path}"
