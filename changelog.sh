#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from git history.
# Usage: bash changelog.sh [output-file]

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

validate_output_path() {
  local path="$1"
  local repo_root="$2"

  if [ -z "${path}" ]; then
    echo "Error: output path cannot be empty." >&2
    exit 1
  fi

  if [ "$(sanitize_plain_text "${path}")" != "${path}" ]; then
    echo "Error: output path contains control characters." >&2
    exit 1
  fi
  case "${path}" in
    *$'\n'*|*$'\r'*|*$'\t'*)
      echo "Error: output path contains whitespace control characters." >&2
      exit 1
      ;;
  esac

  case "${path}" in
    /*)
      echo "Error: output path must be relative, not absolute." >&2
      exit 1
      ;;
    -*|*/-*|*'/../'*|../*|*/..|..|*'//'*)
      echo "Error: output path contains unsafe path components." >&2
      exit 1
      ;;
    *.md)
      ;;
    *)
      echo "Error: output path must end in .md." >&2
      exit 1
      ;;
  esac

  local dir
  dir="$(dirname "${path}")"
  if [ "${dir}" != "." ] && [ ! -d "${dir}" ]; then
    echo "Error: output directory does not exist: ${dir}" >&2
    exit 1
  fi

  if [ -L "${path}" ]; then
    echo "Error: output path must not be a symlink." >&2
    exit 1
  fi

  local repo_root_real parent_real
  repo_root_real="$(cd "${repo_root}" && pwd -P)"
  parent_real="$(cd "${dir}" && pwd -P)"
  case "${parent_real}" in
    "${repo_root_real}"|"${repo_root_real}"/*)
      ;;
    *)
      echo "Error: output directory must stay inside the repository." >&2
      exit 1
      ;;
  esac
}

strip_control_chars() {
  # Remove ASCII control characters except tab/newline/carriage return. Git commit
  # subjects are single-line, but author names and remote URLs may still contain
  # odd bytes when read from adversarial repositories.
  LC_ALL=C tr -d '\000-\010\013\014\016-\037\177'
}

escape_markdown_text() {
  # Keep generated changelogs readable while preventing commit metadata from
  # breaking Markdown links/code spans or injecting raw HTML tags.
  sed \
    -e 's/\\/\\\\/g' \
    -e 's/`/\\`/g' \
    -e 's/\[/\\[/g' \
    -e 's/\]/\\]/g' \
    -e 's/</\\</g' \
    -e 's/>/\\>/g'
}

sanitize_plain_text() {
  printf '%s' "$1" | strip_control_chars
}

sanitize_markdown_text() {
  printf '%s' "$1" | strip_control_chars | escape_markdown_text
}

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

if [ "$(pwd -P)" != "$(cd "${REPO_ROOT}" && pwd -P)" ]; then
  echo "Error: changelog.sh must be run from the repository root." >&2
  exit 1
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "Error: repository has no commits." >&2
  exit 1
fi

validate_output_path "${OUTPUT_FILE}" "${REPO_ROOT}"

LAST_TAG=""
if RAW_LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  # Resolve the raw tag to a commit hash before sanitizing it for display. The
  # --end-of-options marker prevents unusual ref names from being parsed as flags.
  LAST_TAG_COMMIT="$(git rev-parse --verify --end-of-options "${RAW_LAST_TAG}^{commit}")"
  LAST_TAG="$(sanitize_plain_text "${RAW_LAST_TAG}")"
  RANGE="${LAST_TAG_COMMIT}..HEAD"
  SINCE_LABEL="since $(sanitize_markdown_text "${LAST_TAG}")"
else
  RANGE="HEAD"
  SINCE_LABEL="from initial commit"
fi

if [ -n "${LAST_TAG}" ] && [ -z "$(git log --format=%H "${RANGE}")" ]; then
  echo "No commits found since ${LAST_TAG}; writing empty changelog."
fi

TODAY="$(date +%Y-%m-%d)"
REMOTE_URL="$(git config --get remote.origin.url || true)"
if [ -n "${REMOTE_URL}" ]; then
  REPO_NAME="$(basename -- "${REMOTE_URL}" .git)"
else
  REPO_NAME="$(basename "$(git rev-parse --show-toplevel)")"
fi
REPO_NAME="$(sanitize_markdown_text "${REPO_NAME}")"
TMP_DIR="$(mktemp -d)"

ADDED="${TMP_DIR}/added"
FIXED="${TMP_DIR}/fixed"
CHANGED="${TMP_DIR}/changed"
REMOVED="${TMP_DIR}/removed"

cleanup() {
  rm -f "${ADDED}" "${FIXED}" "${CHANGED}" "${REMOVED}"
  rmdir "${TMP_DIR}" 2>/dev/null || true
}
trap cleanup EXIT

: > "${ADDED}"; : > "${FIXED}"; : > "${CHANGED}"; : > "${REMOVED}"

categorize_commit() {
  local subject_lc="$1"
  case "${subject_lc}" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*|*" added "*|*" implement "*|*" implements "*) echo "${ADDED}" ;;
    fix:*|bugfix:*|hotfix:*|*" fix "*|*" fixes "*|*" fixed "*|*" bug "*|*" error "*|*" crash "*) echo "${FIXED}" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|remove\ *|removes\ *|removed\ *|delete\ *|deletes\ *|deleted\ *|*" remove "*|*" removes "*|*" removed "*|*" delete "*|*" deletes "*|*" deleted "*) echo "${REMOVED}" ;;
    *) echo "${CHANGED}" ;;
  esac
}

# Use ASCII unit separators so commit subjects can contain ordinary punctuation safely.
git log --reverse --no-merges --format='%h%x1f%s%x1f%an' "${RANGE}" | while IFS=$'\x1f' read -r short_hash subject author; do
  [ -n "${subject}" ] || continue
  subject_for_category="$(sanitize_plain_text "${subject}")"
  subject_lc="$(printf '%s' "${subject_for_category}" | tr '[:upper:]' '[:lower:]')"
  target_file="$(categorize_commit "${subject_lc}")"
  # Strip common conventional-commit prefixes for cleaner changelog text.
  clean_subject="$(printf '%s' "${subject_for_category}" | sed -E 's/^(feat|feature|fix|bugfix|hotfix|chore|docs|style|refactor|test|perf|ci|build|remove|delete)(\([^)]*\))?!?:[[:space:]]*//I')"
  clean_subject="$(sanitize_markdown_text "${clean_subject}")"
  clean_author="$(sanitize_markdown_text "${author}")"
  printf -- '- %s (`%s`, %s)\n' "${clean_subject}" "${short_hash}" "${clean_author}" >> "${target_file}"
done

write_section() {
  local title="$1"
  local file="$2"
  printf '### %s\n' "${title}"
  if [ -s "${file}" ]; then
    cat "${file}"
  else
    printf -- '- None\n'
  fi
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes to `%s` are documented here.\n\n' "${REPO_NAME}"
  printf 'Generated on %s for commits %s.\n\n' "${TODAY}" "${SINCE_LABEL}"
  printf '## Unreleased - %s\n\n' "${TODAY}"
  write_section "Added" "${ADDED}"
  write_section "Fixed" "${FIXED}"
  write_section "Changed" "${CHANGED}"
  write_section "Removed" "${REMOVED}"
} > "${OUTPUT_FILE}"

echo "Wrote ${OUTPUT_FILE}"
