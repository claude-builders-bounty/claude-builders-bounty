#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history since the last tag.
# Usage: bash changelog.sh [output-file]
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if [[ -z "${REPO_ROOT}" ]]; then
  echo "error: run this inside a git repository" >&2
  exit 1
fi

cd "${REPO_ROOT}"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "${LAST_TAG}" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_LABEL="since ${LAST_TAG}"
else
  FIRST_COMMIT="$(git rev-list --max-parents=0 HEAD | tail -n 1)"
  RANGE="${FIRST_COMMIT}..HEAD"
  # Include the root commit as well when there are no tags
  RANGE_LABEL="full history (no tags found)"
  INCLUDE_ROOT=1
fi

DATE="$(date -u +%Y-%m-%d)"
REPO_NAME="$(basename "${REPO_ROOT}")"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

: >"${TMP_DIR}/added"
: >"${TMP_DIR}/fixed"
: >"${TMP_DIR}/changed"
: >"${TMP_DIR}/removed"
: >"${TMP_DIR}/other"

categorize() {
  local subject="$1"
  local hash="$2"
  local lower entry
  lower="$(printf '%s' "${subject}" | tr '[:upper:]' '[:lower:]')"
  entry="- ${subject} (\`${hash}\`)"

  case "${lower}" in
    feat:*|feat\(*|feature:*|feature\(*|add\ *|added\ *|adding\ *|implement\ *)
      printf '%s\n' "${entry}" >>"${TMP_DIR}/added"
      ;;
    fix:*|fix\(*|bugfix*|hotfix*|fix\ *)
      printf '%s\n' "${entry}" >>"${TMP_DIR}/fixed"
      ;;
    remove:*|remove\(*|removed:*|removed\ *|rm:*|delete:*|deleted\ *|drop:*|dropped\ *|revert:*)
      printf '%s\n' "${entry}" >>"${TMP_DIR}/removed"
      ;;
    change:*|changed:*|update:*|updated\ *|refactor:*|perf:*|improve:*|improved\ *|enhance:*|chore:*|docs:*|style:*|build:*|ci:*|update\ *|refactor\ *|improve\ *|change\ *)
      printf '%s\n' "${entry}" >>"${TMP_DIR}/changed"
      ;;
    *)
      printf '%s\n' "${entry}" >>"${TMP_DIR}/other"
      ;;
  esac
}

# hash<TAB>subject
while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash}" || -z "${subject}" ]] && continue
  categorize "${subject}" "${hash}"
done < <(git log "${RANGE}" --pretty=format:'%h%x09%s' --no-merges)

if [[ "${INCLUDE_ROOT:-0}" == "1" ]]; then
  ROOT_LINE="$(git log -1 --pretty=format:'%h%x09%s' "${FIRST_COMMIT}")"
  ROOT_HASH="${ROOT_LINE%%$'\t'*}"
  ROOT_SUBJECT="${ROOT_LINE#*$'\t'}"
  categorize "${ROOT_SUBJECT}" "${ROOT_HASH}"
fi

{
  echo "# Changelog"
  echo
  echo "## [${DATE}] — ${REPO_NAME}"
  echo
  echo "_Generated ${RANGE_LABEL}_"
  echo

  write_section() {
    local title="$1"
    local file="$2"
    if [[ -s "${file}" ]]; then
      echo "### ${title}"
      echo
      # newest-first already from git log; keep stable order
      cat "${file}"
      echo
    fi
  }

  write_section "Added" "${TMP_DIR}/added"
  write_section "Fixed" "${TMP_DIR}/fixed"
  write_section "Changed" "${TMP_DIR}/changed"
  write_section "Removed" "${TMP_DIR}/removed"

  if [[ -s "${TMP_DIR}/other" ]]; then
    echo "### Changed"
    echo
    echo "_Uncategorized commits (treated as Changed):_"
    echo
    cat "${TMP_DIR}/other"
    echo
  fi

  if [[ ! -s "${TMP_DIR}/added" && ! -s "${TMP_DIR}/fixed" && ! -s "${TMP_DIR}/changed" && ! -s "${TMP_DIR}/removed" && ! -s "${TMP_DIR}/other" ]]; then
    echo "_No commits found in range ${RANGE}_"
    echo
  fi
} >"${OUTPUT}"

echo "Wrote ${OUTPUT} (${RANGE_LABEL})"
