#!/usr/bin/env bash
set -euo pipefail

output="CHANGELOG.md"
since=""
include_hashes=false

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--output CHANGELOG.md] [--since <tag-or-rev>] [--include-hashes]

Generates a structured CHANGELOG.md from commits since the last git tag.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      output="${2:-}"
      shift 2
      ;;
    --since)
      since="${2:-}"
      shift 2
      ;;
    --include-hashes)
      include_hashes=true
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

if ! command -v git >/dev/null 2>&1; then
  echo "git is required but was not found on PATH." >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Run this script from inside a git repository." >&2
  exit 1
fi

if [[ -z "$since" ]]; then
  since="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

range="HEAD"
scope="all history"
if [[ -n "$since" ]]; then
  range="${since}..HEAD"
  scope="commits since ${since}"
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

git log --no-merges --pretty=format:'%s%x09%h' "$range" > "$tmp"

clean_subject() {
  local subject="$1"
  subject="${subject#[[:space:]]}"
  subject="${subject%[[:space:]]}"
  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  printf '%s' "$subject"
}

category_for() {
  local subject
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  case "$subject" in
    feat:*|feat\(*|feature:*|add:*|added:*|new:*)
      printf 'Added'
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|repair:*)
      printf 'Fixed'
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*)
      printf 'Removed'
      ;;
    *)
      if printf '%s' "$subject" | grep -Eq '^(docs|doc|refactor|perf|test|tests|chore|ci|build|style|change|changed)(\(|:)|breaking change'; then
        printf 'Changed'
      else
        printf 'Changed'
      fi
      ;;
  esac
}

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

while IFS=$'\t' read -r subject short_hash; do
  [[ -z "${subject:-}" ]] && continue
  entry="$(clean_subject "$subject")"
  if [[ "$include_hashes" == true ]]; then
    entry="${entry} (${short_hash})"
  fi

  case "$(category_for "$subject")" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
done < "$tmp"

write_section() {
  local title="$1"
  shift
  local items=("$@")

  printf '### %s\n\n' "$title"
  if [[ ${#items[@]} -eq 0 ]]; then
    printf -- '- No entries.\n\n'
    return
  fi

  for item in "${items[@]}"; do
    printf -- '- %s\n' "$item"
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased\n\n'
  printf '_Generated from %s on %s._\n\n' "$scope" "$(date -u +%Y-%m-%d)"
  write_section 'Added' "${added[@]}"
  write_section 'Fixed' "${fixed[@]}"
  write_section 'Changed' "${changed[@]}"
  write_section 'Removed' "${removed[@]}"
} > "$output"

echo "Wrote ${output} from ${scope}."
