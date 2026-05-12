#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if [[ -z "$REPO_ROOT" ]]; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

cd "$REPO_ROOT"

LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LATEST_TAG" ]]; then
  RANGE="${LATEST_TAG}..HEAD"
  RANGE_LABEL="since ${LATEST_TAG}"
else
  RANGE="HEAD"
  RANGE_LABEL="from the first commit"
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "Error: no commits found in this repository." >&2
  exit 1
fi

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

categorize_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*\):*|feature:*|feature\(*\):*|add:*|add\(*\):*|added:*|*' add '*|*' adds '*)
      ADDED+=("$subject")
      ;;
    fix:*|fix\(*\):*|bug:*|bug\(*\):*|bugfix:*|bugfix\(*\):*|hotfix:*|hotfix\(*\):*|*' fix '*|*' fixes '*|*' fixed '*)
      FIXED+=("$subject")
      ;;
    remove:*|remove\(*\):*|removed:*|delete:*|delete\(*\):*|deleted:*|deprecate:*|deprecate\(*\):*|deprecated:*|*' remove '*|*' removes '*|*' delete '*)
      REMOVED+=("$subject")
      ;;
    change:*|change\(*\):*|changed:*|update:*|update\(*\):*|updated:*|refactor:*|refactor\(*\):*|docs:*|docs\(*\):*|test:*|test\(*\):*|style:*|style\(*\):*|chore:*|chore\(*\):*|build:*|build\(*\):*|ci:*|ci\(*\):*|perf:*|perf\(*\):*)
      CHANGED+=("$subject")
      ;;
    *)
      CHANGED+=("$subject")
      ;;
  esac
}

while IFS= read -r subject || [[ -n "$subject" ]]; do
  [[ -z "$subject" ]] && continue
  categorize_commit "$subject"
done < <(git log "$RANGE" --reverse --pretty=format:'%s')

SECTIONS_WRITTEN=0

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  if [[ "$SECTIONS_WRITTEN" -gt 0 ]]; then
    echo >> "$OUTPUT_FILE"
  fi

  {
    echo "### ${title}"
    echo
    if [[ "${#entries[@]}" -eq 0 ]]; then
      echo "- Nothing notable."
    else
      for entry in "${entries[@]}"; do
        echo "- ${entry}"
      done
    fi
  } >> "$OUTPUT_FILE"

  SECTIONS_WRITTEN=$((SECTIONS_WRITTEN + 1))
}

{
  echo "# Changelog"
  echo
  echo "Generated on $(date -u +%Y-%m-%d) for changes ${RANGE_LABEL}."
  echo
  echo "## Unreleased"
  echo
} > "$OUTPUT_FILE"

write_section "Added" "${ADDED[@]}"
write_section "Fixed" "${FIXED[@]}"
write_section "Changed" "${CHANGED[@]}"
write_section "Removed" "${REMOVED[@]}"

echo "Wrote ${OUTPUT_FILE}"
