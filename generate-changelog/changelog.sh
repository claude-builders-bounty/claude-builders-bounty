#!/usr/bin/env bash
set -euo pipefail

OUTPUT="CHANGELOG.md"
FROM_REF=""
TITLE="Unreleased"

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--output CHANGELOG.md] [--from TAG_OR_SHA] [--title TITLE]

Generates a structured changelog from git commits since the latest tag.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      OUTPUT="${2:-}"
      shift 2
      ;;
    --from)
      FROM_REF="${2:-}"
      shift 2
      ;;
    --title)
      TITLE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

if [[ -z "$FROM_REF" ]]; then
  FROM_REF="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -n "$FROM_REF" ]]; then
  RANGE="$FROM_REF..HEAD"
  RANGE_LABEL="since $FROM_REF"
else
  RANGE="HEAD"
  RANGE_LABEL="from repository history (no tags found)"
fi

commit_lines="$(git log "$RANGE" --no-merges --pretty=format:'%h%x09%s' 2>/dev/null || true)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

trim() {
  local value="$1"
  value="${value#${value%%[![:space:]]*}}"
  value="${value%${value##*[![:space:]]}}"
  printf '%s' "$value"
}

humanize_subject() {
  local subject="$1"
  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(trim "$subject")"
  if [[ -z "$subject" ]]; then
    subject="Miscellaneous update"
  fi
  printf '%s' "$subject"
}

add_entry() {
  local category="$1"
  local hash="$2"
  local subject="$3"
  local entry="$(humanize_subject "$subject") ($hash)"

  case "$category" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
    Changed) changed+=("$entry") ;;
  esac
}

categorize() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ ^(feat|feature)(\(.+\))?!?: ]]; then
    printf 'Added'
  elif [[ "$lower" =~ ^(fix|bugfix|hotfix)(\(.+\))?!?: ]]; then
    printf 'Fixed'
  elif [[ "$lower" =~ ^(remove|removed)(\(.+\))?!?: ]] || [[ "$lower" =~ (^|[^a-z])(remove|removed|delete|deleted|deprecate|deprecated)([^a-z]|$) ]]; then
    printf 'Removed'
  elif [[ "$lower" =~ ^(docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?: ]]; then
    printf 'Changed'
  elif [[ "$lower" =~ (^|[^a-z])(add|added|new|introduce|introduced|create|created)([^a-z]|$) ]]; then
    printf 'Added'
  elif [[ "$lower" =~ (^|[^a-z])(fix|fixed|bug|bugfix|resolve|resolved|repair|patched)([^a-z]|$) ]]; then
    printf 'Fixed'
  else
    printf 'Changed'
  fi
}

if [[ -n "$commit_lines" ]]; then
  while IFS=$'\t' read -r hash subject; do
    [[ -z "${hash:-}" ]] && continue
    category="$(categorize "$subject")"
    add_entry "$category" "$hash" "$subject"
  done <<< "$commit_lines"
fi

write_section() {
  local heading="$1"
  shift
  local entries=("$@")
  printf '### %s\n\n' "$heading"
  if [[ ${#entries[@]} -eq 0 ]]; then
    printf -- '- Nothing.\n\n'
  else
    local entry
    for entry in "${entries[@]}"; do
      printf -- '- %s\n' "$entry"
    done
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes generated from git commits %s.\n\n' "$RANGE_LABEL"
  printf '## %s - %s\n\n' "$TITLE" "$(date +%Y-%m-%d)"
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$OUTPUT"

printf 'Generated %s with %d Added, %d Fixed, %d Changed, %d Removed entries.\n' \
  "$OUTPUT" "${#added[@]}" "${#fixed[@]}" "${#changed[@]}" "${#removed[@]}"
