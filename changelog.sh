#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh
Generates CHANGELOG.md from commit messages since the latest git tag.
If no tag exists, it uses the full history.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not inside a git repository" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if last_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${last_tag}..HEAD"
  range_label="since ${last_tag}"
else
  range="--all"
  range_label="from the full history (no tags found)"
fi

extract_section() {
  local text="$1"
  local output

  if [[ "$text" =~ (^|[[:space:]/:-])(feat|feature|add|added|adding|implements?|implemented|initial|create|creates|created)([[:space:]/:-]|$) ]]; then
    output="added"
  elif [[ "$text" =~ (^|[[:space:]/:-])(fix|fixed|fixes|bug|bugs|patch|patched|resolve|resolved|resolves|issue)([[:space:]/:-]|$) ]]; then
    output="fixed"
  elif [[ "$text" =~ (^|[[:space:]/:-])(remove|removed|removing|delete|deleted|drops?|deprecate|deprecates|deprecated|cleanup)([[:space:]/:-]|$) ]]; then
    output="removed"
  else
    output="changed"
  fi

  printf "%s" "$output"
}

shopt -s nocasematch

added=()
fixed=()
changed=()
removed=()
commit_count=0

while IFS= read -r -d '' subject && IFS= read -r -d '' body; do
  title="$subject"
  text="${subject}
${body}"
  section=$(extract_section "$text")

  title="${title//$'\r'/}"
  title="${title//$'\n'/ }"
  title="${title//[$'\t']/ }"

  case "$section" in
    added)
      added+=("${title}")
      ;;
    fixed)
      fixed+=("${title}")
      ;;
    removed)
      removed+=("${title}")
      ;;
    changed)
      changed+=("${title}")
      ;;
  esac

  ((commit_count += 1))
done < <(git log --no-merges --pretty=format:'%s%x00%b%x00' "$range")

render_section() {
  local heading=$1
  shift
  local -a entries=("$@")

  {
    printf -- "\n### %s\n" "$heading"
    if ((${#entries[@]} == 0)); then
      printf -- "- No entries.\n"
    else
      for item in "${entries[@]}"; do
        printf -- "- %s\n" "$item"
      done
    fi
  }
}

{
  echo "# Changelog"
  echo
  echo "## [Unreleased] (${range_label})"
  render_section "Added" "${added[@]+"${added[@]}"}"
  render_section "Fixed" "${fixed[@]+"${fixed[@]}"}"
  render_section "Changed" "${changed[@]+"${changed[@]}"}"
  render_section "Removed" "${removed[@]+"${removed[@]}"}"
} > CHANGELOG.md

echo "Generated CHANGELOG.md with ${commit_count} commits (${range_label})."
