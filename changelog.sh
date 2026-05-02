#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from git commits since the last tag.
# Usage: bash changelog.sh [--output CHANGELOG.md] [--repo .]

OUTPUT="CHANGELOG.md"
REPO="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o)
      OUTPUT="${2:?missing output path}"
      shift 2
      ;;
    --repo|-r)
      REPO="${2:?missing repo path}"
      shift 2
      ;;
    --help|-h)
      echo "Usage: bash changelog.sh [--output CHANGELOG.md] [--repo .]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

cd "$REPO"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "Error: not inside a git repository" >&2
  exit 1
}

LAST_TAG=""
if LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LAST_TAG}..HEAD"
  SINCE="since ${LAST_TAG}"
else
  RANGE="HEAD"
  SINCE="for all commits (no tags found)"
fi

VERSION="Unreleased"
TODAY=$(date +%Y-%m-%d)

COMMITS=$(git log "$RANGE" --no-merges --pretty=format:'%h%x09%s' 2>/dev/null || true)

categorize() {
  local subject="$1"
  local lower
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')

  if [[ "$lower" =~ ^(feat|feature)(\(.+\))?!?: ]] || [[ "$lower" =~ add|create|implement|introduce|support ]]; then
    echo "Added"
  elif [[ "$lower" =~ ^(fix|bugfix|hotfix)(\(.+\))?!?: ]] || [[ "$lower" =~ fix|bug|patch|resolve|correct ]]; then
    echo "Fixed"
  elif [[ "$lower" =~ ^(remove|removed|delete|deleted)(\(.+\))?!?: ]] || [[ "$lower" =~ remove|delete|drop|deprecate ]]; then
    echo "Removed"
  elif [[ "$lower" =~ ^(change|changed|refactor|perf|style|docs|test|ci|build|chore)(\(.+\))?!?: ]] || [[ "$lower" =~ update|change|refactor|improve|rename|bump ]]; then
    echo "Changed"
  else
    echo "Changed"
  fi
}

sanitize_subject() {
  local subject="$1"
  # Strip common Conventional Commit prefixes while keeping the human-readable title.
  printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//'
}

declare -a ADDED=() FIXED=() CHANGED=() REMOVED=()

if [[ -n "${COMMITS}" ]]; then
  while IFS=$'\t' read -r hash subject; do
    [[ -z "${hash:-}" || -z "${subject:-}" ]] && continue
    clean=$(sanitize_subject "$subject")
    entry="- ${clean} (${hash})"
    case "$(categorize "$subject")" in
      Added) ADDED+=("$entry") ;;
      Fixed) FIXED+=("$entry") ;;
      Removed) REMOVED+=("$entry") ;;
      *) CHANGED+=("$entry") ;;
    esac
  done <<< "$COMMITS"
fi

write_section() {
  local title="$1"
  shift
  local -a items=("$@")
  printf '### %s\n\n' "$title"
  if [[ ${#items[@]} -eq 0 ]]; then
    printf -- '- None\n\n'
  else
    printf '%s\n' "${items[@]}"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git history.\n\n'
  printf '## [%s] - %s\n\n' "$VERSION" "$TODAY"
  printf '_Commits %s._\n\n' "$SINCE"
  write_section "Added" "${ADDED[@]}"
  write_section "Fixed" "${FIXED[@]}"
  write_section "Changed" "${CHANGED[@]}"
  write_section "Removed" "${REMOVED[@]}"
} > "$OUTPUT"

printf 'Generated %s from commits %s\n' "$OUTPUT" "$SINCE"
