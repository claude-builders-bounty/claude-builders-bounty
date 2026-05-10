#!/usr/bin/env bash
set -euo pipefail

# Generate a Keep a Changelog style CHANGELOG.md from git commits since the last tag.
# Usage: bash changelog.sh [output-file]

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

git fetch --tags --quiet 2>/dev/null || true

LAST_TAG=""
if LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LAST_TAG}..HEAD"
  SINCE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  SINCE_LABEL="from repository history"
fi

if ! git rev-list --max-count=1 ${RANGE} >/dev/null 2>&1; then
  echo "error: no commits found for range ${RANGE}" >&2
  exit 1
fi

VERSION="Unreleased"
DATE_UTC="$(date -u +%Y-%m-%d)"

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

categorize_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*) echo "ADDED" ;;
    fix:*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" bug "*) echo "FIXED" ;;
    remove:*|removed:*|delete:*|deleted:*|*" remove "*|*" deletes "*) echo "REMOVED" ;;
    refactor:*|perf:*|docs:*|style:*|test:*|ci:*|chore:*|change:*|changed:*|update:*|updated:*|*" update "*) echo "CHANGED" ;;
    *) echo "CHANGED" ;;
  esac
}

while IFS= read -r line; do
  sha="${line%%$'\t'*}"
  subject="${line#*$'\t'}"
  entry="${subject} (${sha})"
  case "$(categorize_commit "$subject")" in
    ADDED) ADDED+=("$entry") ;;
    FIXED) FIXED+=("$entry") ;;
    REMOVED) REMOVED+=("$entry") ;;
    *) CHANGED+=("$entry") ;;
  esac
done < <(git log --reverse --format='%h%x09%s' ${RANGE})

write_section() {
  local title="$1"
  shift
  local items=("$@")
  printf '### %s\n' "$title"
  if [ "${#items[@]}" -eq 0 ]; then
    printf -- '- No changes.\n\n'
  else
    local item
    for item in "${items[@]}"; do
      printf -- '- %s\n' "$item"
    done
    printf '\n'
  fi
}

TMP_FILE="$(mktemp)"
{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git commit history.\n\n'
  printf '## [%s] - %s\n\n' "$VERSION" "$DATE_UTC"
  printf '_Generated from commits %s._\n\n' "$SINCE_LABEL"
  write_section "Added" "${ADDED[@]}"
  write_section "Fixed" "${FIXED[@]}"
  write_section "Changed" "${CHANGED[@]}"
  write_section "Removed" "${REMOVED[@]}"
} > "$TMP_FILE"

mv "$TMP_FILE" "$OUTPUT_FILE"
echo "Generated ${OUTPUT_FILE} from commits ${SINCE_LABEL}."
