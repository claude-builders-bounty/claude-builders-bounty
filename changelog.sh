#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
repo_name="$(basename "$repo_root")"
latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
range=""
heading="Unreleased"

if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  heading="Unreleased changes since ${latest_tag}"
fi

declare -a added fixed changed removed

append_commit() {
  local bucket="$1"
  local subject="$2"
  local body="$3"
  local item="- ${subject}"

  if [[ -n "${body//[[:space:]]/}" ]]; then
    local first_body_line
    first_body_line="$(printf '%s\n' "$body" | sed '/^[[:space:]]*$/d' | head -n 1)"
    [[ -n "$first_body_line" ]] && item+=" — ${first_body_line}"
  fi

  case "$bucket" in
    Added) added+=("$item") ;;
    Fixed) fixed+=("$item") ;;
    Changed) changed+=("$item") ;;
    Removed) removed+=("$item") ;;
  esac
}

categorize() {
  local subject_lc="$1"

  case "$subject_lc" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*|*" introduce"*) printf 'Added' ;;
    fix:*|bug:*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" bug"*) printf 'Fixed' ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|*" remove "*|*" delete "*) printf 'Removed' ;;
    refactor:*|change:*|changed:*|update:*|updated:*|docs:*|doc:*|test:*|ci:*|build:*|chore:*|style:*|perf:*|*" update "*|*" change "*) printf 'Changed' ;;
    *) printf 'Changed' ;;
  esac
}

while IFS=$'\x1f' read -r subject body; do
  [[ -z "${subject//[[:space:]]/}" ]] && continue
  bucket="$(categorize "$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')")"
  append_commit "$bucket" "$subject" "$body"
done < <(git log ${range:+$range} --no-merges --pretty=format:'%s%x1f%b%x1e' | tr '\036' '\n')

write_section() {
  local title="$1"
  shift
  local items=("$@")

  printf '### %s\n' "$title"
  if [[ ${#items[@]} -eq 0 ]]; then
    printf -- '- No changes.\n'
  else
    printf '%s\n' "${items[@]}"
  fi
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes for `%s` are generated from git history.\n\n' "$repo_name"
  printf '## %s\n\n' "$heading"
  write_section 'Added' "${added[@]+${added[@]}}"
  write_section 'Fixed' "${fixed[@]+${fixed[@]}}"
  write_section 'Changed' "${changed[@]+${changed[@]}}"
  write_section 'Removed' "${removed[@]+${removed[@]}}"
  if [[ -n "$latest_tag" ]]; then
    printf '_Commit range: `%s..HEAD`_\n' "$latest_tag"
  else
    printf '_Commit range: full repository history; no git tags found._\n'
  fi
} > "$output_file"

printf 'Generated %s\n' "$output_file"
