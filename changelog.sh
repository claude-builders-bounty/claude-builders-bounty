#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  SINCE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  SINCE_LABEL="from project history"
fi

COMMITS="$(git log --no-merges --pretty=format:'%s|%h' "$RANGE")"

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

clean_subject() {
  local subject="$1"
  subject="${subject#feat: }"
  subject="${subject#feat!: }"
  subject="${subject#fix: }"
  subject="${subject#perf: }"
  subject="${subject#refactor: }"
  subject="${subject#chore: }"
  subject="${subject#docs: }"
  subject="${subject#test: }"
  subject="${subject#remove: }"
  subject="${subject#removed: }"
  subject="${subject#delete: }"
  subject="${subject#deleted: }"
  printf '%s' "$subject"
}

while IFS='|' read -r subject sha; do
  [ -z "${subject:-}" ] && continue
  line="$(clean_subject "$subject") (${sha})"
  case "$subject" in
    feat:*|feat!:*|add:*|added:*)
      ADDED+=("$line")
      ;;
    fix:*|bug:*|bugfix:*)
      FIXED+=("$line")
      ;;
    remove:*|removed:*|delete:*|deleted:*)
      REMOVED+=("$line")
      ;;
    *)
      CHANGED+=("$line")
      ;;
  esac
done <<< "$COMMITS"

write_section() {
  local title="$1"
  shift
  local items=("$@")

  {
    echo "### ${title}"
    echo
    if [ "${#items[@]}" -eq 0 ]; then
      echo "- No changes."
    else
      for item in "${items[@]}"; do
        echo "- ${item}"
      done
    fi
    echo
  } >> "$OUTPUT_FILE"
}

{
  echo "# Changelog"
  echo
  echo "Generated on $(date +%Y-%m-%d) ${SINCE_LABEL}."
  echo
} > "$OUTPUT_FILE"

write_section "Added" "${ADDED[@]}"
write_section "Fixed" "${FIXED[@]}"
write_section "Changed" "${CHANGED[@]}"
write_section "Removed" "${REMOVED[@]}"

echo "Wrote ${OUTPUT_FILE}"
