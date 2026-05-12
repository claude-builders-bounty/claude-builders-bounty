#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
DATE="$(date +%Y-%m-%d)"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$latest_tag" ]]; then
  commit_range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  commit_range="HEAD"
  range_label="from the full git history"
fi

remote_url="$(git remote get-url origin 2>/dev/null || true)"
repo_url=""
if [[ "$remote_url" =~ ^git@github.com:(.+)\.git$ ]]; then
  repo_url="https://github.com/${BASH_REMATCH[1]}"
elif [[ "$remote_url" =~ ^https://github.com/(.+)\.git$ ]]; then
  repo_url="https://github.com/${BASH_REMATCH[1]}"
elif [[ "$remote_url" =~ ^https://github.com/(.+)$ ]]; then
  repo_url="https://github.com/${BASH_REMATCH[1]}"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_commit() {
  local bucket="$1"
  local hash="$2"
  local subject="$3"
  local short_hash
  local entry

  short_hash="$(git rev-parse --short "$hash")"
  subject="${subject//$'\r'/ }"
  subject="${subject//$'\n'/ }"

  if [[ -n "$repo_url" ]]; then
    entry="- ${subject} ([${short_hash}](${repo_url}/commit/${hash}))"
  else
    entry="- ${subject} (${short_hash})"
  fi

  case "$bucket" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    changed) changed+=("$entry") ;;
  esac
}

categorize_subject() {
  local subject_lc
  subject_lc="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  if [[ "$subject_lc" =~ ^(revert|remove|removed|delete|deleted|drop|dropped)(\(.+\))?[:[:space:]-] || "$subject_lc" =~ (remove|delete|drop)[sd]?[[:space:]] ]]; then
    printf 'removed'
  elif [[ "$subject_lc" =~ ^(fix|fixed|bugfix|hotfix|patch)(\(.+\))?[:[:space:]-] || "$subject_lc" =~ (fix|resolve|repair)[sd]?[[:space:]] ]]; then
    printf 'fixed'
  elif [[ "$subject_lc" =~ ^(feat|feature|add|added|new)(\(.+\))?[:[:space:]-] || "$subject_lc" =~ (add|introduce)[sd]?[[:space:]] ]]; then
    printf 'added'
  else
    printf 'changed'
  fi
}

while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue
  bucket="$(categorize_subject "$subject")"
  append_commit "$bucket" "$hash" "$subject"
done < <(git log "$commit_range" --no-merges --pretty=format:'%H%x09%s')

write_section() {
  local title="$1"
  shift
  local -a entries=("$@")

  printf '### %s\n\n' "$title"
  if (( ${#entries[@]} == 0 )); then
    printf -- '- No changes.\n\n'
    return
  fi

  printf '%s\n' "${entries[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git commits %s.\n\n' "$range_label"
  printf '## Unreleased - %s\n\n' "$DATE"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$OUTPUT_FILE"

echo "Generated ${OUTPUT_FILE} ${range_label}."
