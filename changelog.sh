#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must run inside a git repository" >&2
  exit 1
fi

LAST_TAG=""
if LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  RANGE_LABEL="from first commit"
fi

COMMITS=$(git log --no-merges --pretty=format:'%H%x1f%s%x1f%b%x1e' "$RANGE")
DATE=$(date -u +%Y-%m-%d)

classify_commit() {
  local subject_lc
  subject_lc=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')

  case "$subject_lc" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*) echo "Added" ;;
    fix:*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" bug "*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|*" remove "*|*" removes "*|*" delete "*) echo "Removed" ;;
    change:*|changed:*|refactor:*|perf:*|docs:*|test:*|chore:*|build:*|ci:*) echo "Changed" ;;
    *) echo "Changed" ;;
  esac
}

format_subject() {
  local subject="$1"
  subject=${subject#feat: }
  subject=${subject#fix: }
  subject=${subject#docs: }
  subject=${subject#chore: }
  subject=${subject#refactor: }
  subject=${subject#test: }
  subject=${subject#ci: }
  subject=${subject#build: }
  printf '%s' "$subject"
}

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

while IFS=$'\x1f' read -r hash subject body; do
  [ -n "${hash:-}" ] || continue
  short_hash=$(printf '%s' "$hash" | cut -c1-7)
  clean_subject=$(format_subject "$subject")
  entry="- ${clean_subject} (${short_hash})"
  category=$(classify_commit "$subject")
  case "$category" in
    Added) ADDED+=("$entry") ;;
    Fixed) FIXED+=("$entry") ;;
    Removed) REMOVED+=("$entry") ;;
    *) CHANGED+=("$entry") ;;
  esac
done < <(printf '%s\n' "$COMMITS" | tr '\036' '\n')

write_section() {
  local title="$1"
  shift
  local items=("$@")
  printf '### %s\n\n' "$title"
  if [ "${#items[@]}" -eq 0 ]; then
    printf -- '- None\n\n'
  else
    printf '%s\n' "${items[@]}"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf '## %s - %s\n\n' "$DATE" "$RANGE_LABEL"
  write_section "Added" "${ADDED[@]}"
  write_section "Fixed" "${FIXED[@]}"
  write_section "Changed" "${CHANGED[@]}"
  write_section "Removed" "${REMOVED[@]}"
} > "$OUTPUT_FILE"

echo "Generated ${OUTPUT_FILE} (${RANGE_LABEL})"
