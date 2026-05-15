#!/usr/bin/env bash
set -euo pipefail

repo="."
output="CHANGELOG.md"
from_ref=""
to_ref="HEAD"
version=""
dry_run=0

usage() {
  cat <<'USAGE'
Generate a structured CHANGELOG.md from git history.

Usage:
  bash changelog.sh [options]

Options:
  --repo PATH       Repository path. Defaults to current directory.
  --output FILE    Output file. Defaults to CHANGELOG.md.
  --from REF       Start after this tag/commit. Defaults to latest reachable tag.
  --to REF         End at this ref. Defaults to HEAD.
  --version NAME   Section heading. Defaults to "Unreleased - YYYY-MM-DD".
  --dry-run        Print changelog to stdout instead of writing a file.
  -h, --help       Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="$2"
      shift 2
      ;;
    --output)
      output="$2"
      shift 2
      ;;
    --from)
      from_ref="$2"
      shift 2
      ;;
    --to)
      to_ref="$2"
      shift 2
      ;;
    --version)
      version="$2"
      shift 2
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
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git -C "$repo" rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not a git repository: $repo" >&2
  exit 1
fi

if [[ -z "$version" ]]; then
  version="Unreleased - $(date +%Y-%m-%d)"
fi

since_label="the beginning of history"
if [[ -z "$from_ref" ]]; then
  from_ref="$(git -C "$repo" describe --tags --abbrev=0 "$to_ref" 2>/dev/null || true)"
fi

if [[ -n "$from_ref" ]]; then
  range="${from_ref}..${to_ref}"
  since_label="$from_ref"
else
  range="$to_ref"
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_item() {
  local category="$1"
  local subject="$2"
  local hash="$3"
  local item="- ${subject} (${hash})"

  case "$category" in
    added) added+=("$item") ;;
    fixed) fixed+=("$item") ;;
    removed) removed+=("$item") ;;
    changed) changed+=("$item") ;;
  esac
}

classify_subject() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ (^|[[:space:]])(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)(\(|:|[[:space:]]) ]]; then
    printf 'removed'
  elif [[ "$lower" =~ (^|[[:space:]])(fix|fixed|bugfix|resolve|resolved|repair|repaired)(\(|:|[[:space:]]) ]]; then
    printf 'fixed'
  elif [[ "$lower" =~ (^|[[:space:]])(feat|feature|add|added|create|created|implement|implemented|introduce|introduced)(\(|:|[[:space:]]) ]]; then
    printf 'added'
  else
    printf 'changed'
  fi
}

while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash}${subject}" ]] && continue
  category="$(classify_subject "$subject")"
  append_item "$category" "$subject" "$hash"
done < <(git -C "$repo" log --reverse --format='%h%x09%s' "$range")

section_file="$(mktemp)"
final_file="$(mktemp)"
trap 'rm -f "$section_file" "$final_file"' EXIT

write_group() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title" >> "$section_file"
  if [[ ${#entries[@]} -eq 0 ]]; then
    printf -- '- No changes.\n\n' >> "$section_file"
    return
  fi

  printf '%s\n' "${entries[@]}" >> "$section_file"
  printf '\n' >> "$section_file"
}

{
  printf '## %s\n\n' "$version"
  printf '_Changes since %s._\n\n' "$since_label"
} > "$section_file"

write_group "Added" "${added[@]}"
write_group "Fixed" "${fixed[@]}"
write_group "Changed" "${changed[@]}"
write_group "Removed" "${removed[@]}"

if [[ "$dry_run" -eq 1 ]]; then
  printf '# Changelog\n\n'
  cat "$section_file"
  exit 0
fi

output_path="$repo/$output"
if [[ -f "$output_path" ]] && head -n 1 "$output_path" | grep -q '^# Changelog'; then
  {
    head -n 1 "$output_path"
    printf '\n'
    cat "$section_file"
    tail -n +2 "$output_path" | sed '/./,$!d'
  } > "$final_file"
else
  {
    printf '# Changelog\n\n'
    cat "$section_file"
  } > "$final_file"
fi

mv "$final_file" "$output_path"
printf 'Wrote %s\n' "$output_path"
