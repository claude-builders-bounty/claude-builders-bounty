#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history since the last tag.
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "error: not inside a git repository" >&2
  exit 1
}
cd "$REPO_ROOT"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  VERSION_LABEL="Unreleased (since ${LAST_TAG})"
else
  RANGE="HEAD"
  VERSION_LABEL="Unreleased"
fi

# Collect subject lines only (skip merges for cleaner output)
mapfile -t COMMITS < <(
  git log "$RANGE" --no-merges --pretty=format:'%s' 2>/dev/null || true
)

if [[ ${#COMMITS[@]} -eq 0 ]] || [[ -z "${COMMITS[0]:-}" ]]; then
  echo "No commits found since ${LAST_TAG:-repository start}." >&2
  cat > "$OUTPUT" <<EOF
# Changelog

## [${VERSION_LABEL}]

_No commits since last tag._
EOF
  echo "Wrote ${OUTPUT}"
  exit 0
fi

declare -a ADDED=() FIXED=() CHANGED=() REMOVED=()

# Regexes stored in variables so `)` is not parsed as part of `[[ ... ]]`.
RE_CONV='^(feat|feature|fix|bugfix|hotfix|chore|docs|style|refactor|perf|test|build|ci|revert|remove|delete|drop)(\([^)]*\))?!?:'
RE_ADD_PREFIX='^(add|added|adding|create|created|creating|introduce|introduced|implement|implemented|new)([[:space:]:-])'
RE_ADD_WORD='[[:space:]](add|added|adding|create|created)[[:space:]]'
RE_FIX_PREFIX='^(fix|fixed|fixing|bug|hotfix|patch|resolve|resolved)([[:space:]:-])'
RE_FIX_WORD='(bug|hotfix|regression)'
RE_REM_PREFIX='^(remove|removed|removing|delete|deleted|deleting|drop|dropped|dropping|deprecate|deprecated)([[:space:]:-])'
RE_STRIP='^[A-Za-z]+(\([^)]*\))?!?:[[:space:]]*(.*)$'

categorize() {
  local msg="$1"
  local lower
  lower="$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')"

  local type=""
  if [[ "$lower" =~ $RE_CONV ]]; then
    type="${BASH_REMATCH[1]}"
  fi

  case "$type" in
    feat|feature)
      ADDED+=("$msg")
      return
      ;;
    fix|bugfix|hotfix)
      FIXED+=("$msg")
      return
      ;;
    remove|delete|drop)
      REMOVED+=("$msg")
      return
      ;;
    chore|docs|style|refactor|perf|test|build|ci|revert)
      CHANGED+=("$msg")
      return
      ;;
  esac

  if [[ "$lower" =~ $RE_ADD_PREFIX ]] || [[ "$lower" =~ $RE_ADD_WORD ]]; then
    ADDED+=("$msg")
  elif [[ "$lower" =~ $RE_FIX_PREFIX ]] || [[ "$lower" =~ $RE_FIX_WORD ]]; then
    FIXED+=("$msg")
  elif [[ "$lower" =~ $RE_REM_PREFIX ]]; then
    REMOVED+=("$msg")
  else
    CHANGED+=("$msg")
  fi
}

for msg in "${COMMITS[@]}"; do
  [[ -z "$msg" ]] && continue
  categorize "$msg"
done

section() {
  local title="$1"
  shift
  local -n items=$1
  if [[ ${#items[@]} -eq 0 ]]; then
    return
  fi
  echo "### ${title}"
  echo
  for item in "${items[@]}"; do
    local clean="$item"
    if [[ "$clean" =~ $RE_STRIP ]]; then
      clean="${BASH_REMATCH[2]}"
    fi
    clean="$(printf '%s' "${clean:0:1}" | tr '[:lower:]' '[:upper:]')${clean:1}"
    echo "- ${clean}"
  done
  echo
}

{
  echo "# Changelog"
  echo
  echo "All notable changes to this project are documented in this file."
  echo
  echo "Generated from git history"
  if [[ -n "$LAST_TAG" ]]; then
    echo "(commits after \`${LAST_TAG}\`)."
  else
    echo "(full history; no tags found)."
  fi
  echo
  echo "## [${VERSION_LABEL}]"
  echo
  section "Added" ADDED
  section "Fixed" FIXED
  section "Changed" CHANGED
  section "Removed" REMOVED
} > "$OUTPUT"

echo "Wrote ${OUTPUT} (${#COMMITS[@]} commit(s) since ${LAST_TAG:-start})"
