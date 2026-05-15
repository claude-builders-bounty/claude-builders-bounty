#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh: run this inside a git repository" >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  heading="Unreleased - changes since ${last_tag}"
else
  range="HEAD"
  heading="Unreleased - full git history"
fi

commit_lines="$(git log "$range" --pretty=format:'%s' --no-merges)"
if [[ -z "$commit_lines" ]]; then
  {
    echo "# Changelog"
    echo
    echo "## ${heading}"
    echo
    echo "No new non-merge commits found."
  } > "$output_file"
  exit 0
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

normalize_subject() {
  local subject="$1"
  local prefix_re='^(feat|fix|chore|docs|refactor|remove|removed|delete|deleted|change|changed|add|added)(\([^)]+\))?!?:[[:space:]]*(.*)$'
  shopt -s nocasematch
  if [[ "$subject" =~ $prefix_re ]]; then
    printf '%s' "${BASH_REMATCH[3]}"
  else
    printf '%s' "$subject"
  fi
  shopt -u nocasematch
}

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  clean="$(normalize_subject "$subject")"
  conventional_re='(\([^)]+\))?!?:'

  if [[ "$lower" =~ ^(feat|add|added)$conventional_re ]] || [[ "$lower" =~ ^(add|adds|added)[[:space:]] ]] || [[ "$lower" == *" add "* || "$lower" == *" adds "* || "$lower" == *" added "* ]]; then
    added+=("$clean")
  elif [[ "$lower" =~ ^(fix|fixed|bugfix)$conventional_re ]] || [[ "$lower" =~ ^(fix|fixes|fixed)[[:space:]] ]] || [[ "$lower" == *" fix "* || "$lower" == *" fixes "* || "$lower" == *" fixed "* ]]; then
    fixed+=("$clean")
  elif [[ "$lower" =~ ^(remove|removed|delete|deleted)$conventional_re ]] || [[ "$lower" =~ ^(remove|removes|removed|delete|deletes|deleted)[[:space:]] ]] || [[ "$lower" == *" remove "* || "$lower" == *" removes "* || "$lower" == *" deleted "* ]]; then
    removed+=("$clean")
  else
    changed+=("$clean")
  fi
done <<< "$commit_lines"

write_section() {
  local name="$1"
  shift
  local items=("$@")

  echo "### ${name}"
  echo
  if (( ${#items[@]} == 0 )); then
    echo "- None."
  else
    for item in "${items[@]}"; do
      echo "- ${item}"
    done
  fi
  echo
}

{
  echo "# Changelog"
  echo
  echo "## ${heading}"
  echo
  write_section "Added" "${added[@]+"${added[@]}"}"
  write_section "Fixed" "${fixed[@]+"${fixed[@]}"}"
  write_section "Changed" "${changed[@]+"${changed[@]}"}"
  write_section "Removed" "${removed[@]+"${removed[@]}"}"
} > "$output_file"

echo "Wrote ${output_file}"
