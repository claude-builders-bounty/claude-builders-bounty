#!/usr/bin/env bash

set -euo pipefail

repo_path="${1:-.}"
output_path="${2:-CHANGELOG.md}"

if [[ ! -d "$repo_path/.git" ]]; then
  echo "error: '$repo_path' is not a git repository" >&2
  exit 1
fi

if ! git -C "$repo_path" rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "error: repository at '$repo_path' has no commits" >&2
  exit 1
fi

last_tag=""
if git -C "$repo_path" describe --tags --abbrev=0 >/dev/null 2>&1; then
  last_tag="$(git -C "$repo_path" describe --tags --abbrev=0)"
fi

if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
else
  range="HEAD"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

normalize_subject() {
  local subject="$1"
  subject="${subject#"${subject%%[![:space:]]*}"}"
  printf '%s' "$subject"
}

classify_subject() {
  local lower="$1"

  if [[ "$lower" =~ ^(feat|feature|add|adds|added|create|created|introduce|introduced|support|supports|supported)(\(.+\))?[:[:space:]-] ]]; then
    echo "added"
  elif [[ "$lower" =~ ^(fix|fixed|bugfix|bug|resolve|resolved|patch|correct|hotfix)(\(.+\))?[:[:space:]-] ]]; then
    echo "fixed"
  elif [[ "$lower" =~ ^(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)(\(.+\))?[:[:space:]-] ]]; then
    echo "removed"
  else
    echo "changed"
  fi
}

while IFS= read -r raw_subject; do
  subject="$(normalize_subject "$raw_subject")"
  [[ -z "$subject" ]] && continue

  lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  category="$(classify_subject "$lower_subject")"

  case "$category" in
    added) added+=("$subject") ;;
    fixed) fixed+=("$subject") ;;
    changed) changed+=("$subject") ;;
    removed) removed+=("$subject") ;;
  esac
done < <(git -C "$repo_path" log "$range" --no-merges --format=%s)

write_section() {
  local heading="$1"
  shift
  local -a entries=("$@")

  echo "## $heading"

  if [[ "${#entries[@]}" -eq 0 ]]; then
    echo "- None"
  else
    for entry in "${entries[@]}"; do
      echo "- $entry"
    done
  fi

  echo
}

generated_on="$(date -u +%Y-%m-%d)"

{
  echo "# Changelog"
  echo
  echo "## Unreleased - $generated_on"
  echo

  if [[ -n "$last_tag" ]]; then
    echo "_Changes since tag \`$last_tag\`._"
  else
    echo "_Changes from the full repository history (no tags found)._"
  fi

  echo

  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$output_path"

echo "Generated $output_path"
