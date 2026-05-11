#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash changelog.sh [output-file]

Examples:
  bash changelog.sh
  bash changelog.sh docs/CHANGELOG.md
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run this script inside a git repository." >&2
  exit 1
fi

output_file="${1:-CHANGELOG.md}"
latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
today="$(date +%Y-%m-%d)"

if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  range_note="Generated from commits since \`$latest_tag\`."
else
  range="HEAD"
  range_note="Generated from all commits because no tags were found."
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

normalize_subject() {
  local subject="$1"
  subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(printf '%s' "$subject" | sed -E 's/^[*-][[:space:]]*//')"
  printf '%s' "$subject"
}

categorize_subject() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ (^|[^a-z])(remove|removed|removes|delete|deleted|drop|dropped|deprecate|deprecated)([^a-z]|$) ]]; then
    printf 'removed'
  elif [[ "$lower" =~ ^(fix|bugfix|hotfix)(\(.+\))?!?: || "$lower" =~ (^|[^a-z])(fix|fixed|fixes|bug|bugs|resolve|resolved|patch|patched|repair|repaired)([^a-z]|$) ]]; then
    printf 'fixed'
  elif [[ "$lower" =~ ^(feat|feature)(\(.+\))?!?: || "$lower" =~ (^|[^a-z])(add|added|adds|create|created|implement|implemented|support|introduce|introduced)([^a-z]|$) ]]; then
    printf 'added'
  else
    printf 'changed'
  fi
}

while IFS= read -r subject || [[ -n "$subject" ]]; do
  [[ -z "$subject" ]] && continue
  clean_subject="$(normalize_subject "$subject")"
  [[ -z "$clean_subject" ]] && continue

  case "$(categorize_subject "$subject")" in
    added) added+=("$clean_subject") ;;
    fixed) fixed+=("$clean_subject") ;;
    removed) removed+=("$clean_subject") ;;
    *) changed+=("$clean_subject") ;;
  esac
done < <(git log --no-merges --reverse --pretty=format:'%s' "$range")

write_section() {
  local title="$1"
  shift
  local items=("$@")

  printf '### %s\n\n' "$title"
  if [[ "${#items[@]}" -eq 0 ]]; then
    printf -- '- No changes.\n\n'
    return
  fi

  local item
  for item in "${items[@]}"; do
    printf -- '- %s\n' "$item"
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$today"
  printf '%s\n\n' "$range_note"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$output_file"

echo "Wrote $output_file"
