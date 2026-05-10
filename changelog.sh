#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

# Include annotated and lightweight tags. If a repo has no tags, use all history.
LAST_TAG=""
if LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LAST_TAG}..HEAD"
  SINCE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  SINCE_LABEL="from initial commit"
fi

if ! git rev-list --count "$RANGE" >/dev/null 2>&1; then
  echo "Error: could not read git history for range: ${RANGE}" >&2
  exit 1
fi

COMMITS=$(git log "$RANGE" --no-merges --pretty=format:'%H%x1f%s%x1f%an%x1f%ad' --date=short)
TODAY=$(date +%Y-%m-%d)
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")

added=()
fixed=()
changed=()
removed=()

add_entry() {
  local category="$1"
  local subject="$2"
  local sha="$3"
  local author="$4"
  local date="$5"
  local short_sha="${sha:0:7}"
  local entry="- ${subject} (${short_sha}, ${author}, ${date})"

  case "$category" in
    Added) added+=("$entry") ;;
    Fixed) fixed+=("$entry") ;;
    Changed) changed+=("$entry") ;;
    Removed) removed+=("$entry") ;;
  esac
}

categorize() {
  local subject_lower
  subject_lower=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')

  case "$subject_lower" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*|*" implement"*|*" introduce"*) echo "Added" ;;
    fix:*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" bug"*|*" repair"*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|*" remove "*|*" delete "*|*" deprecat"*) echo "Removed" ;;
    *) echo "Changed" ;;
  esac
}

if [[ -n "$COMMITS" ]]; then
  while IFS=$'\x1f' read -r sha subject author date; do
    [[ -z "${sha:-}" ]] && continue
    category=$(categorize "$subject")
    add_entry "$category" "$subject" "$sha" "$author" "$date"
  done <<< "$COMMITS"
fi

write_section() {
  local title="$1"
  local var_name="$2"
  local -n entries="$var_name"

  printf '### %s\n' "$title"
  if ((${#entries[@]} == 0)); then
    printf -- '- No changes.\n\n'
  else
    printf '%s\n' "${entries[@]}"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes for `%s` are listed here.\n\n' "$REPO_NAME"
  printf '## Unreleased - %s\n\n' "$TODAY"
  printf '_Generated from git history %s._\n\n' "$SINCE_LABEL"
  write_section "Added" added
  write_section "Fixed" fixed
  write_section "Changed" changed
  write_section "Removed" removed
} > "$OUTPUT_FILE"

echo "Generated ${OUTPUT_FILE} (${SINCE_LABEL})."
