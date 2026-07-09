#!/usr/bin/env bash
# changelog.sh — Generate a Keep a Changelog style CHANGELOG.md from git history.
# Usage: bash changelog.sh [output_file]
#        ./changelog.sh
#
# Fetches commits since the last git tag (or all commits if untagged),
# auto-categorizes into Added / Fixed / Changed / Removed, and writes CHANGELOG.md.

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# --- helpers -----------------------------------------------------------------

category_for() {
  local msg
  msg="$(echo "$1" | tr '[:upper:]' '[:lower:]')"

  # Conventional commit type (optionally scoped): type(scope)!: subject
  local type=""
  if [[ "$msg" =~ ^([a-z]+)(\([^)]*\))?\!?: ]]; then
    type="${BASH_REMATCH[1]}"
  fi

  case "$type" in
    feat|feature|add|adds|added)
      echo "Added"; return ;;
    fix|bugfix|bug|hotfix|patch)
      echo "Fixed"; return ;;
    remove|removed|rm|delete|deleted|deprecate|deprecated)
      echo "Removed"; return ;;
    refactor|style|perf|performance|chore|build|ci|revert|change|changed|update|updated)
      echo "Changed"; return ;;
  esac

  # Keyword fallback for non-conventional messages
  if echo "$msg" | grep -Eqi '(^|[^a-z])(add|added|introduce|introduces|new feature|implement|implements|create|creates)([^a-z]|$)'; then
    echo "Added"; return
  fi
  if echo "$msg" | grep -Eqi '(^|[^a-z])(fix|fixed|bug|hotfix|patch|resolve|resolves)([^a-z]|$)'; then
    echo "Fixed"; return
  fi
  if echo "$msg" | grep -Eqi '(^|[^a-z])(remove|removed|delete|deleted|drop|dropped|deprecate)([^a-z]|$)'; then
    echo "Removed"; return
  fi
  if echo "$msg" | grep -Eqi '(^|[^a-z])(change|changed|update|updated|refactor|improve|improves|rename|renamed)([^a-z]|$)'; then
    echo "Changed"; return
  fi

  # Default bucket
  echo "Changed"
}

clean_subject() {
  # Strip conventional-commit prefix and trailing PR refs for cleaner bullets
  local s="$1"
  s="$(echo "$s" | sed -E 's/^[A-Za-z]+(\([^)]*\))?\!?:[[:space:]]*//')"
  s="$(echo "$s" | sed -E 's/[[:space:]]*\(#[0-9]+\)$//')"
  # Capitalize first letter if present
  if [[ -n "$s" ]]; then
    local first rest
    first="$(echo "${s:0:1}" | tr '[:lower:]' '[:upper:]')"
    rest="${s:1}"
    s="${first}${rest}"
  fi
  echo "$s"
}

# --- resolve range -----------------------------------------------------------

LAST_TAG=""
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

VERSION="Unreleased"
RANGE=""
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  # Next version hint from tag (v1.2.3 -> keep as display name for unreleased)
  VERSION="Unreleased"
else
  RANGE=""  # all commits
fi

# Remote URL for optional commit links
REMOTE_URL=""
if git remote get-url origin >/dev/null 2>&1; then
  REMOTE_URL="$(git remote get-url origin 2>/dev/null | sed -E 's#^git@([^:]+):#https://\1/#; s#\.git$##')"
fi

TODAY="$(date +%Y-%m-%d 2>/dev/null || date '+%Y-%m-%d')"

# --- collect commits ---------------------------------------------------------

# Format: hash<TAB>subject
LOG_ARGS=(--no-merges --pretty=format:'%h%x09%s')
if [[ -n "$RANGE" ]]; then
  mapfile -t COMMITS < <(git log $RANGE "${LOG_ARGS[@]}" 2>/dev/null || true)
else
  mapfile -t COMMITS < <(git log "${LOG_ARGS[@]}" 2>/dev/null || true)
fi

declare -a ADDED=() FIXED=() CHANGED=() REMOVED=()

for line in "${COMMITS[@]:-}"; do
  [[ -z "${line// }" ]] && continue
  hash="${line%%$'\t'*}"
  subject="${line#*$'\t'}"
  [[ -z "$subject" || "$subject" == "$hash" ]] && continue

  cat="$(category_for "$subject")"
  cleaned="$(clean_subject "$subject")"
  [[ -z "$cleaned" ]] && cleaned="$subject"

  if [[ -n "$REMOTE_URL" ]]; then
    bullet="- ${cleaned} (\`${hash}\`)"
  else
    bullet="- ${cleaned} (\`${hash}\`)"
  fi

  case "$cat" in
    Added)   ADDED+=("$bullet") ;;
    Fixed)   FIXED+=("$bullet") ;;
    Removed) REMOVED+=("$bullet") ;;
    *)       CHANGED+=("$bullet") ;;
  esac
done

# --- render ------------------------------------------------------------------

{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project are documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
  echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
  echo ""

  if [[ -n "$LAST_TAG" ]]; then
    echo "## [${VERSION}] - ${TODAY}"
    echo ""
    echo "_Commits since \`${LAST_TAG}\`._"
    echo ""
  else
    echo "## [${VERSION}] - ${TODAY}"
    echo ""
    echo "_Generated from full git history (no tags found)._"
    echo ""
  fi

  write_section() {
    local title="$1"
    shift
    local -a items=("$@")
    if ((${#items[@]} > 0)); then
      echo "### ${title}"
      echo ""
      for item in "${items[@]}"; do
        echo "$item"
      done
      echo ""
    fi
  }

  write_section "Added" "${ADDED[@]:-}"
  write_section "Fixed" "${FIXED[@]:-}"
  write_section "Changed" "${CHANGED[@]:-}"
  write_section "Removed" "${REMOVED[@]:-}"

  # Always show empty category stubs only if nothing was categorized at all
  total=$(( ${#ADDED[@]:-0} + ${#FIXED[@]:-0} + ${#CHANGED[@]:-0} + ${#REMOVED[@]:-0} ))
  if (( total == 0 )); then
    echo "_No commits found in range._"
    echo ""
  fi

  if [[ -n "$LAST_TAG" ]]; then
    echo "---"
    echo ""
    echo "Previous release tag: \`${LAST_TAG}\`"
    echo ""
  fi
} > "$OUTPUT_FILE"

echo "Wrote ${OUTPUT_FILE}"
echo "  Range : ${RANGE:-FULL HISTORY}"
echo "  Tag   : ${LAST_TAG:-<none>}"
echo "  Counts: Added=${#ADDED[@]:-0} Fixed=${#FIXED[@]:-0} Changed=${#CHANGED[@]:-0} Removed=${#REMOVED[@]:-0}"
