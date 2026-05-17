#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
since_ref=""
stdout=false

usage() {
  cat <<'USAGE'
Usage: bash generate-changelog/changelog.sh [--output FILE] [--since REF] [--stdout]

Generates a structured CHANGELOG.md from git commits since the latest tag.

Options:
  --output FILE  Write changelog to FILE instead of CHANGELOG.md
  --since REF    Use REF as the starting point instead of the latest tag
  --stdout       Print changelog instead of writing a file
  -h, --help     Show this help message
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      output_file="${2:-}"
      [[ -n "$output_file" ]] || { echo "Missing value for --output" >&2; exit 1; }
      shift 2
      ;;
    --since)
      since_ref="${2:-}"
      [[ -n "$since_ref" ]] || { echo "Missing value for --since" >&2; exit 1; }
      shift 2
      ;;
    --stdout)
      stdout=true
      shift
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

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "This script must be run inside a git repository." >&2
  exit 1
}

if [[ -z "$since_ref" ]]; then
  since_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$since_ref" ]]; then
  git rev-parse --verify "$since_ref^{commit}" >/dev/null 2>&1 || {
    echo "Could not resolve --since ref: $since_ref" >&2
    exit 1
  }
  range="$since_ref..HEAD"
  range_label="since $since_ref"
else
  range="HEAD"
  range_label="all commits"
fi

categorize_commit() {
  local subject="$1"
  local normalized
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    revert*|remove*|removed*|delete*|deleted*|deprecate*|deprecated*|*": remove "*|*": delete "*)
      printf 'Removed'
      ;;
    fix*|bug*|hotfix*|patch*|*": fix "*|*": bug "*)
      printf 'Fixed'
      ;;
    feat*|feature*|add*|added*|create*|created*|implement*|implemented*|initial*|*": add "*|*": feat "*)
      printf 'Added'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

escape_markdown() {
  printf '%s' "$1" | sed 's/`/\\`/g'
}

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

while IFS=$'\t' read -r hash subject; do
  [[ -n "${hash:-}" && -n "${subject:-}" ]] || continue
  short_hash="${hash:0:7}"
  entry="- $(escape_markdown "$subject") (${short_hash})"

  case "$(categorize_commit "$subject")" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
done < <(git log --no-merges --reverse --format='%H%x09%s' "$range")

emit_section() {
  local title="$1"
  shift
  local -a items=("$@")

  printf '## %s\n\n' "$title"
  if [[ ${#items[@]} -eq 0 ]]; then
    printf -- '- No changes.\n\n'
    return
  fi

  local item
  for item in "${items[@]}"; do
    printf '%s\n' "$item"
  done
  printf '\n'
}

changelog="$(
  printf '# Changelog\n\n'
  printf 'Generated on %s from %s.\n\n' "$(date +%Y-%m-%d)" "$range_label"
  emit_section "Added" "${added[@]}"
  emit_section "Fixed" "${fixed[@]}"
  emit_section "Changed" "${changed[@]}"
  emit_section "Removed" "${removed[@]}"
)"

if [[ "$stdout" == true ]]; then
  printf '%s\n' "$changelog"
else
  printf '%s\n' "$changelog" > "$output_file"
  printf 'Wrote %s\n' "$output_file"
fi
