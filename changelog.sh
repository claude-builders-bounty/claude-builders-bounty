#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
PRINT_STDOUT=0
FETCH_TAGS="${CHANGELOG_FETCH_TAGS:-1}"
SINCE_REF=""

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [options]

Generate CHANGELOG.md from commits since the latest reachable git tag.

Options:
  -o, --output FILE   Write changelog to FILE (default: CHANGELOG.md)
      --stdout        Print changelog instead of writing a file
      --since REF     Use REF..HEAD instead of auto-detecting the latest tag
      --no-fetch      Do not run git fetch --tags before reading tags
  -h, --help          Show this help message
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --stdout)
      PRINT_STDOUT=1
      shift
      ;;
    --since)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      SINCE_REF="$2"
      shift 2
      ;;
    --no-fetch)
      FETCH_TAGS=0
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

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository." >&2
  exit 1
fi

if [[ "$FETCH_TAGS" != "0" ]] && git remote >/dev/null 2>&1 && [[ -n "$(git remote)" ]]; then
  git fetch --tags --quiet 2>/dev/null || true
fi

latest_tag=""
range="HEAD"
range_note="all commits"

if [[ -n "$SINCE_REF" ]]; then
  if ! git rev-parse --verify --quiet "${SINCE_REF}^{commit}" >/dev/null; then
    echo "Reference not found: $SINCE_REF" >&2
    exit 1
  fi
  latest_tag="$SINCE_REF"
  range="${SINCE_REF}..HEAD"
  range_note="commits since ${SINCE_REF}"
else
  latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$latest_tag" ]]; then
    range="${latest_tag}..HEAD"
    range_note="commits since ${latest_tag}"
  fi
fi

repo_url="$(git config --get remote.origin.url || true)"
repo_url="${repo_url%.git}"
if [[ "$repo_url" == git@github.com:* ]]; then
  repo_url="https://github.com/${repo_url#git@github.com:}"
fi

today="$(date +%Y-%m-%d)"
tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

trim_subject() {
  local subject="$1"
  subject="${subject#*): }"
  subject="${subject#*: }"
  subject="${subject#- }"
  printf '%s' "$subject"
}

format_entry() {
  local hash="$1"
  local subject="$2"
  local clean_subject
  clean_subject="$(trim_subject "$subject")"

  if [[ -n "$repo_url" && "$repo_url" == https://github.com/* ]]; then
    printf -- '- %s ([%s](%s/commit/%s))' "$clean_subject" "$hash" "$repo_url" "$hash"
  else
    printf -- '- %s (%s)' "$clean_subject" "$hash"
  fi
}

categorize() {
  local subject="$1"
  local lowered
  lowered="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lowered" in
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*|revert:*)
      printf 'Removed'
      return
      ;;
    fix:*|fix\(*|bugfix:*|hotfix:*|repair:*|resolve:*|resolved:*)
      printf 'Fixed'
      return
      ;;
    feat:*|feat\(*|feature:*|add:*|added:*|implement:*|implemented:*|introduce:*|support:*)
      printf 'Added'
      return
      ;;
    change:*|changed:*|update:*|updated:*|refactor:*|refactor\(*|perf:*|performance:*|docs:*|doc:*|style:*|chore:*|build:*|ci:*|test:*|tests:*)
      printf 'Changed'
      return
      ;;
  esac

  if [[ "$lowered" =~ (^|[[:space:]])(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)([[:space:]]|$) ]]; then
    printf 'Removed'
  elif [[ "$lowered" =~ (^|[[:space:]])(fix|fixed|bug|bugs|error|crash|resolve|resolved|broken)([[:space:]]|$) ]]; then
    printf 'Fixed'
  elif [[ "$lowered" =~ (^|[[:space:]])(add|added|create|created|implement|implemented|introduce|introduced|support|new|initial)([[:space:]]|$) ]]; then
    printf 'Added'
  else
    printf 'Changed'
  fi
}

while IFS=$'\t' read -r hash subject || [[ -n "$hash" ]]; do
  [[ -n "$hash" ]] || continue
  entry="$(format_entry "$hash" "$subject")"
  case "$(categorize "$subject")" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
done < <(git log --no-merges --date=short --pretty=format:'%h%x09%s' "$range")

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  if [[ ${#entries[@]} -eq 0 ]]; then
    return
  fi

  {
    printf '### %s\n\n' "$title"
    printf '%s\n' "${entries[@]}"
    printf '\n'
  } >> "$tmp_file"
}

{
  printf '# Changelog\n\n'
  printf '## [Unreleased] - %s\n\n' "$today"
  printf '_Generated from %s._\n\n' "$range_note"
} > "$tmp_file"

if [[ ${#added[@]} -eq 0 && ${#fixed[@]} -eq 0 && ${#changed[@]} -eq 0 && ${#removed[@]} -eq 0 ]]; then
  printf 'No changes found.\n' >> "$tmp_file"
else
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
fi

if [[ "$PRINT_STDOUT" == "1" ]]; then
  cat "$tmp_file"
else
  cp "$tmp_file" "$OUTPUT_FILE"
  printf 'Wrote %s from %s.\n' "$OUTPUT_FILE" "$range_note"
fi
