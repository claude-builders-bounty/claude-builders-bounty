#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
since_ref=""

usage() {
  cat <<'USAGE'
Usage: bash skills/generate-changelog/changelog.sh [--output CHANGELOG.md] [--since TAG]

Generates a structured CHANGELOG.md from git commits since the latest tag.

Options:
  --output PATH   Write changelog to PATH. Default: CHANGELOG.md
  --since TAG     Use TAG as the starting point instead of the latest tag
  -h, --help      Show this help text
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      if [[ $# -lt 2 ]]; then
        echo "error: --output requires a path" >&2
        exit 2
      fi
      output_file="$2"
      shift 2
      ;;
    --since)
      if [[ $# -lt 2 ]]; then
        echo "error: --since requires a tag or ref" >&2
        exit 2
      fi
      since_ref="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if [[ -n "$since_ref" ]]; then
  if ! git rev-parse --verify --quiet "$since_ref^{commit}" >/dev/null; then
    echo "error: --since ref not found: $since_ref" >&2
    exit 1
  fi
  latest_tag="$since_ref"
elif latest_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  :
else
  latest_tag=""
fi

if [[ -n "$latest_tag" ]]; then
  range="$latest_tag..HEAD"
  range_label="since $latest_tag"
else
  range="HEAD"
  range_label="from repository history"
fi

today="$(date +%Y-%m-%d)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

clean_subject() {
  local subject="$1"
  subject="${subject#[[:space:]]}"
  subject="${subject%[[:space:]]}"
  subject="$(printf '%s' "$subject" | sed -E 's/^(feat|fix|chore|docs|refactor|perf|test|style|build|ci|remove|revert)(\([^)]+\))?!?:[[:space:]]*//')"
  printf '%s' "$subject"
}

entry_for_commit() {
  local hash="$1"
  local subject="$2"
  local short_hash
  short_hash="$(git rev-parse --short "$hash")"
  printf -- "- %s (%s)" "$(clean_subject "$subject")" "$short_hash"
}

categorize_commit() {
  local hash="$1"
  local subject="$2"
  local body="$3"
  local normalized
  normalized="$(printf '%s\n%s' "$subject" "$body" | tr '[:upper:]' '[:lower:]')"
  local entry
  entry="$(entry_for_commit "$hash" "$subject")"

  if [[ "$normalized" =~ (^|[^a-z])(remove|removed|removes|delete|deleted|deletes|drop|dropped|drops|deprecate|deprecated)([^a-z]|$) ]]; then
    removed+=("$entry")
  elif [[ "$normalized" =~ (^|[^a-z])(fix|fixed|fixes|bug|bugfix|hotfix|patch|security|cve)([^a-z]|$) ]]; then
    fixed+=("$entry")
  elif [[ "$normalized" =~ (^|[^a-z])(feat|feature|add|added|adds|new|introduce|introduced|introduces|initial)([^a-z]|$) ]]; then
    added+=("$entry")
  else
    changed+=("$entry")
  fi
}

commit_count=0
while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash:-}" ]] && continue
  body="$(git log -1 --format=%b "$hash")"
  categorize_commit "$hash" "$subject" "$body"
  commit_count=$((commit_count + 1))
done < <(git log --no-merges --reverse --format=$'%H\t%s' "$range")

write_section() {
  local title="$1"
  local array_name="$2"
  local -n items="$array_name"

  printf '### %s\n\n' "$title"
  if [[ "${#items[@]}" -eq 0 ]]; then
    printf -- "- No entries.\n\n"
    return
  fi

  local item
  for item in "${items[@]}"; do
    printf '%s\n' "$item"
  done
  printf '\n'
}

mkdir -p "$(dirname "$output_file")"

{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git history. Review before release.\n\n'
  printf '## Unreleased - %s\n\n' "$today"
  printf '_Changes %s._\n\n' "$range_label"

  if [[ "$commit_count" -eq 0 ]]; then
    printf 'No commits found %s.\n\n' "$range_label"
  fi

  write_section "Added" added
  write_section "Fixed" fixed
  write_section "Changed" changed
  write_section "Removed" removed
} > "$output_file"

printf 'Generated %s from %d commit(s) %s.\n' "$output_file" "$commit_count" "$range_label"
printf 'Added: %d, Fixed: %d, Changed: %d, Removed: %d\n' \
  "${#added[@]}" "${#fixed[@]}" "${#changed[@]}" "${#removed[@]}"
