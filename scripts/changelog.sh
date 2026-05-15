#!/usr/bin/env bash
set -eo pipefail

usage() {
  cat <<'EOF'
Usage: bash scripts/changelog.sh [--output CHANGELOG.md] [--since REF]

Generate a Keep a Changelog-style CHANGELOG.md from git history.

Options:
  --output FILE   Write changelog to FILE (default: CHANGELOG.md)
  --since REF     Start after REF instead of the latest git tag
  --help          Show this help
EOF
}

output_file="CHANGELOG.md"
since_ref=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      output_file="${2:?missing value for --output}"
      shift 2
      ;;
    --since)
      since_ref="${2:?missing value for --since}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run this script inside a git repository." >&2
  exit 1
fi

if [[ -z "$since_ref" ]]; then
  since_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$since_ref" ]]; then
  git rev-parse --verify --quiet "$since_ref^{commit}" >/dev/null || {
    echo "Error: --since '$since_ref' is not a valid git ref." >&2
    exit 1
  }
  range="$since_ref..HEAD"
  range_label="since $since_ref"
else
  range="HEAD"
  range_label="from project start"
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
generated_date="$(date +%Y-%m-%d)"

declare -a added fixed changed removed

add_entry() {
  local bucket="$1"
  local entry="$2"
  case "$bucket" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Changed) changed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
  esac
}

categorize_subject() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    revert:*|remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|*breaking\ change*|*deprecat*)
      printf 'Removed'
      ;;
    fix:*|fixed:*|bugfix:*|hotfix:*|repair:*|patch:*|*fix*|*bug*)
      printf 'Fixed'
      ;;
    feat:*|feature:*|add:*|added:*|create:*|created:*|new:*|init:*|initial:*)
      printf 'Added'
      ;;
    refactor:*|change:*|changed:*|update:*|updated:*|improve:*|improved:*|docs:*|doc:*|style:*|test:*|chore:*|ci:*|build:*|perf:*)
      printf 'Changed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

while IFS= read -r commit || [[ -n "$commit" ]]; do
  [[ -z "$commit" ]] && continue

  sha="${commit%%$'\t'*}"
  subject="${commit#*$'\t'}"
  bucket="$(categorize_subject "$subject")"
  entry="$subject (${sha})"
  add_entry "$bucket" "$entry"
done < <(git log "$range" --no-merges --date-order --pretty=format:'%h%x09%s')

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n' "$title"
  if [[ ${#entries[@]} -eq 0 ]]; then
    printf -- '- No changes.\n\n'
    return
  fi

  local item
  for item in "${entries[@]}"; do
    printf -- '- %s\n' "$item"
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes for `%s` are generated from git history.\n\n' "$repo_name"
  printf '## Unreleased - %s\n\n' "$generated_date"
  printf '_Generated %s._\n\n' "$range_label"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$output_file"

printf 'Generated %s (%s).\n' "$output_file" "$range_label"
