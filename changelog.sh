#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! command -v git >/dev/null 2>&1; then
  echo "error: git is required" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: run this script inside a git repository" >&2
  exit 1
fi

LAST_TAG=""
if LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  RANGE="${LAST_TAG}..HEAD"
  SINCE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  SINCE_LABEL="from repository start"
fi

if ! git rev-list --max-count=1 ${RANGE} >/dev/null 2>&1; then
  echo "No commits found for range ${RANGE}." >&2
  exit 0
fi

TMP_FILE="$(mktemp)"
trap 'rm -f "${TMP_FILE}"' EXIT

git log ${RANGE} --no-merges --pretty=format:'%s%x09%h' > "${TMP_FILE}"

bucket_for_subject() {
  local subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "${subject}" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*|*" introduce"*|*" implement"*)
      printf 'Added'
      ;;
    fix:*|bugfix:*|hotfix:*|*" fix"*|*" fixes"*|*" bug"*|*" patch"*)
      printf 'Fixed'
      ;;
    remove:*|removed:*|delete:*|deleted:*|*" remove"*|*" removes"*|*" delete"*|*" deprecate"*)
      printf 'Removed'
      ;;
    change:*|changed:*|refactor:*|update:*|updated:*|docs:*|doc:*|chore:*|style:*|test:*|ci:*)
      printf 'Changed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

section_lines() {
  local section="$1"
  local found=0
  while IFS=$'\t' read -r subject hash; do
    [ -z "${subject}" ] && continue
    if [ "$(bucket_for_subject "${subject}")" = "${section}" ]; then
      printf -- '- %s (%s)\n' "${subject}" "${hash}"
      found=1
    fi
  done < "${TMP_FILE}"
  if [ "${found}" -eq 0 ]; then
    printf -- '- No changes.\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'Generated from git history %s on %s.\n\n' "${SINCE_LABEL}" "$(date +%Y-%m-%d)"
  for section in Added Fixed Changed Removed; do
    printf '## %s\n\n' "${section}"
    section_lines "${section}"
    printf '\n'
  done
} > "${OUTPUT_FILE}"

printf 'Wrote %s using commits %s.\n' "${OUTPUT_FILE}" "${SINCE_LABEL}"
