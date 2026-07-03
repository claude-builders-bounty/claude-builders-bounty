#!/usr/bin/env bash
set -euo pipefail

# Generate a Keep-a-Changelog-style CHANGELOG.md from commits since the last tag.
# Usage:
#   bash changelog.sh [output-file]
#   bash changelog.sh CHANGELOG.md

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

LAST_TAG=""
if LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  RANGE="${LAST_TAG}..HEAD"
  SINCE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  SINCE_LABEL="for full history (no git tags found)"
fi

TODAY="$(date +%Y-%m-%d)"
VERSION="Unreleased"

map_category() {
  local subject_lc="$1"
  case "$subject_lc" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*|*" implement "*|*" create "*) echo "Added" ;;
    fix:*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" bug "*|*" repair "*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|*" remove "*|*" delete "*|*" drop "*) echo "Removed" ;;
    *) echo "Changed" ;;
  esac
}

# Read commits as hash<TAB>subject. Using --reverse gives chronological order.
COMMITS="$(git log --reverse --pretty=format:'%h%x09%s' ${RANGE})"

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

if [[ -n "${COMMITS}" ]]; then
  while IFS=$'\t' read -r hash subject; do
    [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue
    subject_lc="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
    line="- ${subject} (${hash})"
    case "$(map_category "$subject_lc")" in
      Added) ADDED+=("$line") ;;
      Fixed) FIXED+=("$line") ;;
      Removed) REMOVED+=("$line") ;;
      *) CHANGED+=("$line") ;;
    esac
  done <<< "${COMMITS}"
fi

write_section() {
  local title="$1"; shift
  local -n items_ref=$1
  printf '### %s\n' "$title"
  if ((${#items_ref[@]} == 0)); then
    printf -- '- No entries.\n\n'
  else
    printf '%s\n' "${items_ref[@]}"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git commit history.\n\n'
  printf '## [%s] - %s\n\n' "$VERSION" "$TODAY"
  printf '_Generated %s._\n\n' "$SINCE_LABEL"
  write_section "Added" ADDED
  write_section "Fixed" FIXED
  write_section "Changed" CHANGED
  write_section "Removed" REMOVED
} > "$OUTPUT_FILE"

printf 'Generated %s from commits %s\n' "$OUTPUT_FILE" "$SINCE_LABEL"
