#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   ./changelog.sh [since-ref] [output-file]
#
# Defaults:
#   since-ref   = last git tag (or the first commit if no tags exist)
#   output-file = CHANGELOG.md
#
# Categories:
#   Added, Fixed, Changed, Removed (Keep a Changelog conventions)
#
set -euo pipefail

# Resolve the git repo root (the script is meant to run from inside a repo).
REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null || echo "$(pwd)")"
SINCE_REF="${1:-}"
OUTPUT_FILE="${2:-CHANGELOG.md}"

# --- Determine the "since" ref -------------------------------------------
if [[ -z "$SINCE_REF" ]]; then
  LAST_TAG="$(git -C "$REPO_DIR" describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$LAST_TAG" ]]; then
    SINCE_REF="$LAST_TAG"
  else
    # No tags: start from the first commit ever.
    SINCE_REF="$(git -C "$REPO_DIR" rev-list --max-parents=0 HEAD)"
  fi
fi

# --- Collect commits since ref --------------------------------------------
# Format: <short-hash>|<subject>
mapfile -t COMMITS < <(git -C "$REPO_DIR" log --pretty=format:'%h|%s' "$SINCE_REF..HEAD" 2>/dev/null || true)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
  echo "No commits found since '$SINCE_REF'. Nothing to generate."
  exit 0
fi

# --- Categorize -----------------------------------------------------------
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=() OTHER=()

categorize() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    add*|new*|feature*|implement*|introduce*|initial*|create*|support*|feat*)
      ADDED+=("$subject") ;;
    fix*|bug*|resolve*|patch*|repair*|hotfix*|correct*|revert*)
      FIXED+=("$subject") ;;
    remove*|delete*|drop*|deprecat*|cleanup*)
      REMOVED+=("$subject") ;;
    change*|update*|refactor*|improve*|rewrite*|migrate*|rename*|bump*|upgrade*|enhance*|perf*|docs*|chore*|style*|build*|ci*|test*)
      CHANGED+=("$subject") ;;
    *)
      OTHER+=("$subject") ;;
  esac
}

for entry in "${COMMITS[@]}"; do
  subject="${entry#*|}"
  categorize "$subject"
done

# --- Render ---------------------------------------------------------------
VERSION="Unreleased"
if [[ "$SINCE_REF" != "$(git -C "$REPO_DIR" rev-list --max-parents=0 HEAD)" ]]; then
  VERSION="$SINCE_REF..HEAD"
fi

TODAY="$(date +%Y-%m-%d)"
{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project are documented in this file.\n\n'
  printf '## [%s] - %s\n\n' "$VERSION" "$TODAY"

  emit_section() {
    local name="$1"; shift
    local items=("$@")
    if [[ ${#items[@]} -gt 0 ]]; then
      printf '### %s\n\n' "$name"
      for item in "${items[@]}"; do
        printf -- '- %s\n' "$item"
      done
      printf '\n'
    fi
  }

  emit_section "Added"   "${ADDED[@]}"
  emit_section "Fixed"   "${FIXED[@]}"
  emit_section "Changed" "${CHANGED[@]}"
  emit_section "Removed" "${REMOVED[@]}"
  emit_section "Other"   "${OTHER[@]}"
} > "$OUTPUT_FILE"

echo "CHANGELOG.md generated with ${#COMMITS[@]} commit(s) since '$SINCE_REF'."
