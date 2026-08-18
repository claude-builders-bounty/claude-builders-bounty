#!/usr/bin/env bash

set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! repository_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  printf 'Error: run this command inside a Git repository.\n' >&2
  exit 1
fi

cd "$repository_root"

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  log_range="${last_tag}..HEAD"
  history_note="since tag $last_tag"
else
  log_range="HEAD"
  history_note="from the beginning of the repository history"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

categorize() {
  local subject="${1,,}"
  local added_regex='^(feat|feature|add|added|new|create|created)(\([^)]*\))?:'
  local fixed_regex='^(fix|fixed|bug|bugfix|hotfix|patch)(\([^)]*\))?:'
  local removed_regex='^(remove|removed|delete|deleted|drop|dropped)(\([^)]*\))?:'
  if [[ "$subject" =~ $added_regex ]]; then
    printf 'Added'
  elif [[ "$subject" =~ $fixed_regex ]]; then
    printf 'Fixed'
  elif [[ "$subject" =~ $removed_regex ]]; then
    printf 'Removed'
  else
    printf 'Changed'
  fi
}

clean_subject() {
  # Remove a conventional-commit prefix while keeping the human-readable text.
  printf '%s' "$1" | sed -E 's/^[[:alpha:]]+(\([^)]*\))?:[[:space:]]*//'
}

while IFS=$'\x1f' read -r commit_hash commit_subject; do
  [[ -z "$commit_hash" ]] && continue

  short_hash="${commit_hash:0:7}"
  entry="- $(clean_subject "$commit_subject") (${short_hash})"
  case "$(categorize "$commit_subject")" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    Changed) changed+=("$entry") ;;
  esac
done < <(git log --no-merges --format='%H%x1f%s' "$log_range")

mkdir -p "$(dirname "$output_file")"
{
  printf '# Changelog\n\n'
  printf '> Generated automatically from Git history %s.\n\n' "$history_note"
  printf '## [Unreleased]\n\n'

  has_changes=0
  for category in Added Fixed Changed Removed; do
    case "$category" in
      Added) entries=("${added[@]-}") ;;
      Fixed) entries=("${fixed[@]-}") ;;
      Changed) entries=("${changed[@]-}") ;;
      Removed) entries=("${removed[@]-}") ;;
    esac

    if ((${#entries[@]} > 0)) && [[ -n "${entries[0]:-}" ]]; then
      has_changes=1
      printf '### %s\n\n' "$category"
      printf '%s\n' "${entries[@]}"
      printf '\n'
    fi
  done

  if ((has_changes == 0)); then
    printf '_No changes found._\n'
  fi
} > "$output_file"

printf 'Generated %s\n' "$output_file"
