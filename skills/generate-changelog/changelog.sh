#!/usr/bin/env bash
set -eo pipefail

output_file="CHANGELOG.md"
version="Unreleased"
since_ref=""

usage() {
  cat <<'USAGE'
Generate a structured changelog from git history.

Usage:
  bash skills/generate-changelog/changelog.sh [--output FILE] [--version VERSION] [--since REF]

Options:
  --output FILE     Changelog path to write. Default: CHANGELOG.md
  --version VERSION Section title to use. Default: Unreleased
  --since REF       Git ref/tag to collect commits after. Default: latest tag, or all commits.
  -h, --help        Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      output_file="${2:-}"
      shift 2
      ;;
    --version)
      version="${2:-}"
      shift 2
      ;;
    --since)
      since_ref="${2:-}"
      shift 2
      ;;
    -h|--help)
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

if [[ -z "$output_file" || -z "$version" ]]; then
  echo "--output and --version require non-empty values" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This command must be run inside a git repository." >&2
  exit 1
fi

if [[ -z "$since_ref" ]]; then
  since_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$since_ref" ]]; then
  if ! git rev-parse --verify "${since_ref}^{commit}" >/dev/null 2>&1; then
    echo "Could not resolve --since ref: $since_ref" >&2
    exit 1
  fi
  commit_range="${since_ref}..HEAD"
  range_note="Changes since ${since_ref}"
else
  commit_range="HEAD"
  range_note="Changes from all available commits"
fi

commits=()
while IFS= read -r commit; do
  if [[ -n "$commit" ]]; then
    commits+=("$commit")
  fi
done < <(git log --no-merges --reverse --pretty=format:'%s (%h)%n' "$commit_range")

today="$(date +%F)"
tmp_file="$(mktemp)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

normalize_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#*] }"
  printf '%s' "$subject"
}

append_commit() {
  local subject="$1"
  local lowered
  lowered="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  local item
  item="$(normalize_subject "$subject")"

  case "$lowered" in
    feat:*|feature:*|add:*|added:*|*' add '*|*' adds '*)
      added+=("$item")
      ;;
    fix:*|fixed:*|bugfix:*|bug:*|hotfix:*|*' fix '*|*' fixes '*)
      fixed+=("$item")
      ;;
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|deprecated:*|*' remove '*|*' delete '*)
      removed+=("$item")
      ;;
    chore:*|refactor:*|perf:*|style:*|docs:*|test:*|ci:*|build:*|change:*|changed:*|update:*|updated:*)
      changed+=("$item")
      ;;
    *)
      changed+=("$item")
      ;;
  esac
}

for commit in "${commits[@]}"; do
  append_commit "$commit"
done

write_section() {
  local title="$1"
  shift
  local items=("$@")

  if [[ ${#items[@]} -eq 0 ]]; then
    return
  fi

  {
    printf '### %s\n\n' "$title"
    for item in "${items[@]}"; do
      printf -- '- %s\n' "$item"
    done
    printf '\n'
  } >> "$tmp_file"
}

{
  printf '# Changelog\n\n'
  printf '## [%s] - %s\n\n' "$version" "$today"
  printf '_%s._\n\n' "$range_note"
} > "$tmp_file"

if [[ ${#commits[@]} -eq 0 ]]; then
  printf '_No commits found for this range._\n' >> "$tmp_file"
else
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
fi

mv "$tmp_file" "$output_file"
echo "Wrote $output_file"
