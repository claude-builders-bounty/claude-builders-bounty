#!/usr/bin/env bash
set -eo pipefail

OUTPUT_FILE="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
TODAY="$(date +%Y-%m-%d)"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "${LAST_TAG}" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  RANGE_LABEL="from full history"
fi

COMMITS_FILE="$(mktemp)"
trap 'rm -f "${COMMITS_FILE}"' EXIT
git log "${RANGE}" --reverse --format='%s' > "${COMMITS_FILE}" 2>/dev/null || true

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

trim_scope() {
  local subject="$1"
  subject="${subject#feat: }"
  subject="${subject#feat!: }"
  subject="${subject#fix: }"
  subject="${subject#chore: }"
  subject="${subject#refactor: }"
  subject="${subject#docs: }"
  subject="${subject#test: }"
  subject="${subject#remove: }"
  subject="${subject#removed: }"
  subject="${subject#delete: }"
  subject="${subject#deleted: }"
  echo "${subject}"
}

add_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "${subject}" | tr '[:upper:]' '[:lower:]')"
  local item
  item="$(trim_scope "${subject}")"

  if [[ "${lower}" =~ ^(feat|add)(\(.+\))?!?:|(^|[[:space:]])(add|adds|added|new)[[:space:]] ]]; then
    ADDED+=("${item}")
  elif [[ "${lower}" =~ ^fix(\(.+\))?!?:|(^|[[:space:]])(fix|fixes|fixed|bugfix|bug)[[:space:]] ]]; then
    FIXED+=("${item}")
  elif [[ "${lower}" =~ ^(remove|delete)(\(.+\))?!?:|(^|[[:space:]])(remove|removes|removed|delete|deletes|deleted)[[:space:]] ]]; then
    REMOVED+=("${item}")
  else
    CHANGED+=("${item}")
  fi
}

render_section() {
  local title="$1"
  shift
  local items=("$@")

  printf '### %s\n\n' "${title}"
  if [[ "${#items[@]}" -eq 0 ]]; then
    printf -- '- No changes.\n\n'
    return
  fi

  for item in "${items[@]}"; do
    printf -- '- %s\n' "${item}"
  done
  printf '\n'
}

while IFS= read -r commit; do
  [[ -z "${commit}" ]] && continue
  add_commit "${commit}"
done < "${COMMITS_FILE}"

COMMIT_COUNT="$(grep -c . "${COMMITS_FILE}" || true)"

{
  printf '# Changelog\n\n'
  printf '## [Unreleased] - %s\n\n' "${TODAY}"
  printf '_Generated from git history %s._\n\n' "${RANGE_LABEL}"

  if [[ "${COMMIT_COUNT}" -eq 0 ]]; then
    printf 'No commits found for this range.\n'
    exit 0
  fi

  render_section "Added" "${ADDED[@]}"
  render_section "Fixed" "${FIXED[@]}"
  render_section "Changed" "${CHANGED[@]}"
  render_section "Removed" "${REMOVED[@]}"
} > "${OUTPUT_FILE}"

echo "Generated ${OUTPUT_FILE} from ${COMMIT_COUNT} commit(s) ${RANGE_LABEL}."
