#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
from_ref=""
dry_run=0
include_merges=0

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash changelog.sh [options]

Options:
  -o, --output FILE     Write changelog to FILE (default: CHANGELOG.md)
      --from REF        Use REF instead of the latest reachable git tag
      --include-merges  Include merge commits
      --dry-run         Print the changelog to stdout without writing a file
  -h, --help            Show this help
USAGE
}

die() {
  printf 'changelog: %s\n' "$*" >&2
  exit 1
}

while (($#)); do
  case "$1" in
    -o|--output)
      [[ $# -ge 2 ]] || die "$1 requires a file path"
      output_file="$2"
      shift 2
      ;;
    --from)
      [[ $# -ge 2 ]] || die "$1 requires a git ref"
      from_ref="$2"
      shift 2
      ;;
    --include-merges)
      include_merges=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1"
      ;;
  esac
done

command -v git >/dev/null 2>&1 || die "git is required"

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || die "run this inside a git repository"
cd "$repo_root"

git rev-parse --verify HEAD >/dev/null 2>&1 || die "repository has no commits"

latest_ref=""
range_label="repository start"
if [[ -n "$from_ref" ]]; then
  git rev-parse --verify "$from_ref^{commit}" >/dev/null 2>&1 || die "ref not found: $from_ref"
  latest_ref="$from_ref"
  range_label="$from_ref"
else
  latest_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$latest_ref" ]]; then
    range_label="$latest_ref"
  fi
fi

range_args=()
if [[ -n "$latest_ref" ]]; then
  range_args=("${latest_ref}..HEAD")
else
  range_args=("HEAD")
fi

merge_args=()
if [[ "$include_merges" -eq 0 ]]; then
  merge_args=(--no-merges)
fi

classify_subject() {
  local subject="$1"
  local lower
  local prefix
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  prefix="${lower%%:*}"

  case "$prefix" in
    feat|feat!*|feat\(*|feature|feature!*|feature\(*)
      printf 'Added'
      return
      ;;
    fix|fix!*|fix\(*)
      printf 'Fixed'
      return
      ;;
    remove|remove!*|remove\(*|delete|delete!*|delete\(*|drop|drop!*|drop\(*|deprecate|deprecate!*|deprecate\(*)
      printf 'Removed'
      return
      ;;
  esac

  case "$lower" in
    add\ *|adds\ *|added\ *|create\ *|creates\ *|created\ *|implement\ *|implements\ *|implemented\ *|introduce\ *|introduces\ *|introduced\ *|support\ *|supports\ *|supported\ *)
      printf 'Added'
      return
      ;;
    fix\ *|fixes\ *|fixed\ *|resolve\ *|resolves\ *|resolved\ *|correct\ *|corrects\ *|corrected\ *|patch\ *|patches\ *|patched\ *)
      printf 'Fixed'
      return
      ;;
    remove\ *|removes\ *|removed\ *|delete\ *|deletes\ *|deleted\ *|drop\ *|drops\ *|dropped\ *|deprecate\ *|deprecates\ *|deprecated\ *|revert\ *|reverts\ *|reverted\ *)
      printf 'Removed'
      return
      ;;
  esac

  printf 'Changed'
}

normalize_subject() {
  local subject="$1"
  local summary="$subject"

  summary="${summary//$'\r'/}"
  summary="${summary//$'\t'/ }"

  summary="$(printf '%s' "$summary" | sed -E 's/^[A-Za-z][A-Za-z0-9_-]*(\([^)]*\))?!?:[[:space:]]*//')"

  summary="${summary#"${summary%%[![:space:]]*}"}"
  summary="${summary%"${summary##*[![:space:]]}"}"

  if [[ -z "$summary" ]]; then
    summary="$subject"
  fi

  printf '%s' "${summary:0:1}" | tr '[:lower:]' '[:upper:]'
  printf '%s' "${summary:1}"
}

append_entry() {
  local category="$1"
  local entry="$2"

  case "$category" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
}

write_section() {
  local title="$1"
  shift

  printf '### %s\n\n' "$title"
  if (($# == 0)); then
    printf -- '- No changes.\n\n'
    return
  fi

  local entry
  for entry in "$@"; do
    printf '%s\n' "$entry"
  done
  printf '\n'
}

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()
declare -a commit_rows=()

mapfile -t commit_rows < <(
  git log "${range_args[@]}" "${merge_args[@]}" --reverse --pretty=format:'%h%x09%s'
)

for row in "${commit_rows[@]}"; do
  hash="${row%%$'\t'*}"
  subject="${row#*$'\t'}"
  category="$(classify_subject "$subject")"
  summary="$(normalize_subject "$subject")"
  append_entry "$category" "- ${summary} (\`${hash}\`)"
done

today="$(date +%F)"
tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$today"
  if [[ -n "$latest_ref" ]]; then
    printf 'Generated from commits after `%s`.\n\n' "$range_label"
  else
    printf 'Generated from all commits because no git tag was found.\n\n'
  fi

  write_section 'Added' "${added[@]}"
  write_section 'Fixed' "${fixed[@]}"
  write_section 'Changed' "${changed[@]}"
  write_section 'Removed' "${removed[@]}"
} > "$tmp_file"

if [[ "$dry_run" -eq 1 ]]; then
  cat "$tmp_file"
else
  mkdir -p "$(dirname "$output_file")"
  mv "$tmp_file" "$output_file"
  trap - EXIT
  printf 'Wrote %s from %s commit(s) since %s.\n' "$output_file" "${#commit_rows[@]}" "$range_label"
fi
