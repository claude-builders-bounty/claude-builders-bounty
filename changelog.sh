#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [output-file]

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

LAST_TAG=""
if LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  RANGE_LABEL="from all commits (no git tags found)"
fi

if ! git rev-list --max-count=1 "$RANGE" >/dev/null 2>&1; then
  echo "No commits found for ${RANGE_LABEL}." >&2
  exit 0
fi

commit_lines=$(git log --no-merges --reverse --pretty=format:'%s|%h' "$RANGE")

added=()
fixed=()
changed=()
removed=()

add_item() {
  local bucket="$1"
  local subject="$2"
  local hash="$3"
  local item="- ${subject} (${hash})"

  case "$bucket" in
    added) added+=("$item") ;;
    fixed) fixed+=("$item") ;;
    changed) changed+=("$item") ;;
    removed) removed+=("$item") ;;
  esac
}

categorize() {
  local subject="$1"
  local lower
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')

  case "$lower" in
    feat:*|feat\(*|feature:*|add:*|added:*|*" add "*|*" adds "*|*" added "*)
      printf 'added'
      ;;
    fix:*|fix\(*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" fixed "*|*bug*)
      printf 'fixed'
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|*" remove "*|*" removes "*|*" removed "*|*" delete "*)
      printf 'removed'
      ;;
    change:*|changed:*|refactor:*|refactor\(*|perf:*|perf\(*|chore:*|chore\(*|docs:*|docs\(*|style:*|test:*|ci:*)
      printf 'changed'
      ;;
    *)
      printf 'changed'
      ;;
  esac
}

while IFS='|' read -r subject hash; do
  [ -z "${subject}" ] && continue
  bucket=$(categorize "$subject")
  add_item "$bucket" "$subject" "$hash"
done <<< "$commit_lines"

write_section() {
  local title="$1"
  local array_name="$2"
  local -n entries="$array_name"

  printf '## %s\n\n' "$title"
  if [ "${#entries[@]}" -eq 0 ]; then
    printf -- '- No changes.\n\n'
  else
    printf '%s\n' "${entries[@]}"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'Generated from git history %s on %s.\n\n' "$RANGE_LABEL" "$(date -u +%Y-%m-%d)"
  write_section "Added" added
  write_section "Fixed" fixed
  write_section "Changed" changed
  write_section "Removed" removed
} > "$OUTPUT_FILE"

echo "Generated ${OUTPUT_FILE} ${RANGE_LABEL}."
