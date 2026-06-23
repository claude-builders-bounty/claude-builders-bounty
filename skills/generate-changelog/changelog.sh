#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag=""
range="HEAD"
if latest_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range="${latest_tag}..HEAD"
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
generated_at="$(date +%Y-%m-%d)"
commit_count="$(git rev-list --count "$range" 2>/dev/null || echo 0)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

categorize_commit() {
  local subject="$1"
  local lowered
  lowered="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lowered" in
    feat:*|feat"("*"):"*|feature:*|add:*|create:*|introduce:*)
      printf '%s\n' "added"
      ;;
    fix:*|fix"("*"):"*|bugfix:*|repair:*|resolve:*|patch:*)
      printf '%s\n' "fixed"
      ;;
    remove:*|remove"("*"):"*|delete:*|delete"("*"):"*|drop:*|drop"("*"):"*|deprecate:*|deprecate"("*"):"*)
      printf '%s\n' "removed"
      ;;
    *)
      if [[ "$lowered" =~ (^|[[:space:]])(add|adds|added|create|creates|created|introduce|introduces|introduced)([[:space:]]|$) ]]; then
        printf '%s\n' "added"
      elif [[ "$lowered" =~ (^|[[:space:]])(fix|fixes|fixed|repair|repairs|repaired|resolve|resolves|resolved|patch|patched)([[:space:]]|$) ]]; then
        printf '%s\n' "fixed"
      elif [[ "$lowered" =~ (^|[[:space:]])(remove|removes|removed|delete|deletes|deleted|drop|drops|dropped|deprecate|deprecates|deprecated)([[:space:]]|$) ]]; then
        printf '%s\n' "removed"
      else
        printf '%s\n' "changed"
      fi
      ;;
  esac
}

append_entry() {
  local category="$1"
  local entry="$2"

  case "$category" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    changed) changed+=("$entry") ;;
  esac
}

while IFS=$'\t' read -r hash date subject || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" ]] && continue
  category="$(categorize_commit "$subject")"
  append_entry "$category" "- ${subject} (${hash}, ${date})"
done < <(git log "$range" --pretty=format:'%h%x09%cs%x09%s')

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  if ((${#entries[@]} == 0)); then
    return
  fi

  printf '### %s\n\n' "$title"
  printf '%s\n' "${entries[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated for `%s` on %s.\n\n' "$repo_name" "$generated_at"
  if [[ -n "$latest_tag" ]]; then
    printf '## Unreleased\n\n'
    printf 'Changes since `%s` (%s commits).\n\n' "$latest_tag" "$commit_count"
  else
    printf '## Initial History\n\n'
    printf 'No git tags were found, so this changelog includes all reachable commits (%s commits).\n\n' "$commit_count"
  fi

  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"

  if ((commit_count == 0)); then
    printf 'No commits found for the selected range.\n'
  fi
} > "$output_file"

echo "Wrote $output_file"
