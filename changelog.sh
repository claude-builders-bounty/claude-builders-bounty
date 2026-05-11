#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
repo_name="$(basename "$repo_root")"
generated_on="$(date -u +%Y-%m-%d)"

range="${CHANGELOG_RANGE:-}"
range_label=""

if [[ -n "$range" ]]; then
  range_label="for range $range"
else
  latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$latest_tag" ]]; then
    range="${latest_tag}..HEAD"
    range_label="since $latest_tag"
  else
    range=""
    range_label="for all git history"
  fi
fi

remote_url="$(git config --get remote.origin.url 2>/dev/null || true)"
commit_base_url=""
if [[ "$remote_url" =~ ^git@github.com:(.*)\.git$ ]]; then
  commit_base_url="https://github.com/${BASH_REMATCH[1]}/commit"
elif [[ "$remote_url" =~ ^https://github.com/(.*)\.git$ ]]; then
  commit_base_url="https://github.com/${BASH_REMATCH[1]}/commit"
elif [[ "$remote_url" =~ ^https://github.com/(.*)$ ]]; then
  commit_base_url="https://github.com/${BASH_REMATCH[1]}/commit"
fi

added=()
fixed=()
changed=()
removed=()

append_commit() {
  local category="$1"
  local hash="$2"
  local subject="$3"
  local short_hash="${hash:0:7}"
  local bullet="- ${subject}"

  if [[ -n "$commit_base_url" ]]; then
    bullet="${bullet} ([${short_hash}](${commit_base_url}/${hash}))"
  else
    bullet="${bullet} (${short_hash})"
  fi

  case "$category" in
    added) added+=("$bullet") ;;
    fixed) fixed+=("$bullet") ;;
    removed) removed+=("$bullet") ;;
    *) changed+=("$bullet") ;;
  esac
}

categorize_subject() {
  local subject_lower
  subject_lower="$(printf "%s" "$1" | tr "[:upper:]" "[:lower:]")"

  case "$subject_lower" in
    feat* | add* | create*) printf "%s" "added" ;;
    fix* | bug* | patch*) printf "%s" "fixed" ;;
    remove* | delete* | drop*) printf "%s" "removed" ;;
    *) printf "%s" "changed" ;;
  esac
}

while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash:-}" ]] && continue
  category="$(categorize_subject "$subject")"
  append_commit "$category" "$hash" "$subject"
done < <(git log --reverse --no-merges --format='%H%x09%s' ${range})

write_section() {
  local title="$1"
  shift

  printf "## %s\n\n" "$title"
  if [[ "$#" -eq 0 ]]; then
    printf -- "- None\n"
  else
    printf "%s\n" "$@"
  fi
  printf "\n"
}

{
  printf "# Changelog\n\n"
  printf "Generated on %s for \`%s\` %s.\n\n" "$generated_on" "$repo_name" "$range_label"
  if [[ "${#added[@]}" -gt 0 ]]; then
    write_section "Added" "${added[@]}"
  else
    write_section "Added"
  fi
  if [[ "${#fixed[@]}" -gt 0 ]]; then
    write_section "Fixed" "${fixed[@]}"
  else
    write_section "Fixed"
  fi
  if [[ "${#changed[@]}" -gt 0 ]]; then
    write_section "Changed" "${changed[@]}"
  else
    write_section "Changed"
  fi
  if [[ "${#removed[@]}" -gt 0 ]]; then
    write_section "Removed" "${removed[@]}"
  else
    write_section "Removed"
  fi
} >"$output_file"

echo "Wrote ${output_file}"
