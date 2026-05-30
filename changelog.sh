#!/usr/bin/env bash
set -euo pipefail

output_file="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
today="$(date +%Y-%m-%d)"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

git fetch --tags --quiet 2>/dev/null || true

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  since_label="since ${last_tag}"
else
  range="HEAD"
  since_label="from initial history"
fi

mapfile -t commits < <(git log "$range" --no-merges --format='%s' 2>/dev/null || true)

added=()
fixed=()
changed=()
removed=()

clean_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#*:}"
  subject="${subject#- }"
  printf '%s' "$subject"
}

add_entry() {
  local bucket="$1"
  local subject
  subject="$(clean_subject "$2")"
  [[ -z "$subject" ]] && return

  case "$bucket" in
    added) added+=("$subject") ;;
    fixed) fixed+=("$subject") ;;
    changed) changed+=("$subject") ;;
    removed) removed+=("$subject") ;;
  esac
}

for commit in "${commits[@]}"; do
  lower="$(printf '%s' "$commit" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    feat:*|feat\(*|add:*|added:*|create:*|implement:*)
      add_entry added "$commit"
      ;;
    fix:*|fix\(*|fixed:*|bug:*|repair:*|resolve:*)
      add_entry fixed "$commit"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*)
      add_entry removed "$commit"
      ;;
    *)
      add_entry changed "$commit"
      ;;
  esac
done

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  {
    echo "### ${title}"
    echo
    if [[ "${#entries[@]}" -eq 0 ]]; then
      echo "- No entries."
    else
      for entry in "${entries[@]}"; do
        echo "- ${entry}"
      done
    fi
    echo
  } >> "$output_file"
}

{
  echo "# Changelog"
  echo
  echo "All notable changes are grouped from git commit history."
  echo
  echo "## Unreleased - ${today}"
  echo
  echo "_Generated ${since_label}._"
  echo
} > "$output_file"

if [[ "${#commits[@]}" -eq 0 ]]; then
  {
    echo "No changes found ${since_label}."
    echo
  } >> "$output_file"
else
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
fi

echo "Wrote ${output_file}"
