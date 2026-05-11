#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: changelog.sh [--repo PATH] [--output FILE] [--from REF] [--to REF]

Generate a structured CHANGELOG.md from git history.

Options:
  --repo PATH     Git repository to inspect. Defaults to current directory.
  --output FILE   Output file path. Defaults to CHANGELOG.md in the repo.
  --from REF      Starting ref. Defaults to the latest reachable tag.
  --to REF        Ending ref. Defaults to HEAD.
  -h, --help      Show this help.
USAGE
}

repo="."
output=""
from_ref=""
to_ref="HEAD"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --output)
      output="${2:-}"
      shift 2
      ;;
    --from)
      from_ref="${2:-}"
      shift 2
      ;;
    --to)
      to_ref="${2:-}"
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

if [[ ! -d "$repo/.git" ]] && ! git -C "$repo" rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository: $repo" >&2
  exit 1
fi

if [[ -z "$output" ]]; then
  output="$repo/CHANGELOG.md"
fi

if [[ -z "$from_ref" ]]; then
  from_ref="$(git -C "$repo" describe --tags --abbrev=0 "$to_ref" 2>/dev/null || true)"
fi

range="$to_ref"
range_label="full history through $to_ref"
if [[ -n "$from_ref" ]]; then
  range="$from_ref..$to_ref"
  range_label="$from_ref..$to_ref"
fi

added_file="$(mktemp)"
fixed_file="$(mktemp)"
changed_file="$(mktemp)"
removed_file="$(mktemp)"
breaking_file="$(mktemp)"
trap 'rm -f "$added_file" "$fixed_file" "$changed_file" "$removed_file" "$breaking_file"' EXIT

strip_type() {
  local subject="$1"
  subject="${subject#*!: }"
  subject="$(printf '%s' "$subject" | sed -E 's/^[A-Za-z]+(\([^)]+\))?!?:[[:space:]]*//')"
  printf '%s' "$subject"
}

append_item() {
  local file="$1"
  local hash="$2"
  local subject="$3"
  local clean_subject
  clean_subject="$(strip_type "$subject")"
  printf -- '- %s (`%s`)\n' "$clean_subject" "${hash:0:7}" >> "$file"
}

while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}${subject:-}" ]]; do
  [[ -z "${hash:-}" ]] && continue
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  breaking_regex='^[[:alpha:]]+(\([^)]+\))?!:'
  commit_type="$(printf '%s' "$normalized" | sed -E 's/^([a-z]+)(\([^)]+\))?!?:.*/\1/')"

  if [[ "$subject" =~ $breaking_regex ]] || [[ "$normalized" == *"breaking change"* ]]; then
    append_item "$breaking_file" "$hash" "$subject"
  fi

  case "$commit_type" in
    remove|removed|delete|deleted|deprecate|drop\ *|remove\ *|removed\ *|delete\ *|deleted\ *|deprecate\ *)
      append_item "$removed_file" "$hash" "$subject"
      ;;
    fix|fixed|bug|bugfix|patch|resolve|correct|fix\ *|fixes\ *|fixed\ *|bugfix\ *|resolve\ *|resolved\ *|correct\ *)
      append_item "$fixed_file" "$hash" "$subject"
      ;;
    feat|feature|add|added|create|implement|init|add\ *|adds\ *|added\ *|create\ *|creates\ *|implement\ *|implements\ *|enable\ *)
      append_item "$added_file" "$hash" "$subject"
      ;;
    *)
      append_item "$changed_file" "$hash" "$subject"
      ;;
  esac
done < <(git -C "$repo" log --reverse --pretty=format:'%H%x09%s' "$range")

section() {
  local title="$1"
  local file="$2"
  if [[ -s "$file" ]]; then
    printf '\n### %s\n\n' "$title"
    cat "$file"
  fi
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$(date +%Y-%m-%d)"
  printf '_Generated from `%s`._\n' "$range_label"

  if [[ ! -s "$added_file" && ! -s "$fixed_file" && ! -s "$changed_file" && ! -s "$removed_file" ]]; then
    printf '\nNo commits found for this range.\n'
  else
    section "Added" "$added_file"
    section "Fixed" "$fixed_file"
    section "Changed" "$changed_file"
    section "Removed" "$removed_file"
    section "Breaking Changes" "$breaking_file"
  fi
} > "$output"

echo "Wrote $output"
