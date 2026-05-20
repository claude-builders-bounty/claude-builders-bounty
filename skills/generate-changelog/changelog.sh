#!/usr/bin/env bash
#
# changelog.sh — Generate a Keep-a-Changelog section from git history.
#
# Usage:   ./changelog.sh [VERSION]
# Example: ./changelog.sh v1.3.0 > NEW_SECTION.md
#
# If VERSION is omitted, prints "[unreleased]" as the heading.
# Reads commits between the most recent tag and HEAD; falls back to full history
# when no tags exist.
#
# Classification rules (commit-message prefix, case-insensitive):
#   feat|feature|add        -> Added
#   fix|bug|bugfix|hotfix   -> Fixed
#   refactor|chore|style|perf|docs|ci|build|test -> Changed
#   revert|remove|deprecate -> Removed
#   anything else / none    -> Changed

set -euo pipefail

VERSION="${1:-unreleased}"
TODAY="$(date -u +%Y-%m-%d)"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not inside a git repository" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -z "${LAST_TAG}" ]]; then
  RANGE=""
else
  RANGE="${LAST_TAG}..HEAD"
fi

# Tempfiles for each section.
ADDED="$(mktemp)"
FIXED="$(mktemp)"
CHANGED="$(mktemp)"
REMOVED="$(mktemp)"
trap 'rm -f "$ADDED" "$FIXED" "$CHANGED" "$REMOVED"' EXIT

# Pull commits as SHA<TAB>SUBJECT
while IFS=$'\t' read -r sha subject; do
  [[ -z "${sha}" ]] && continue

  prefix="$(echo "${subject%%:*}" | tr '[:upper:]' '[:lower:]')"
  prefix="${prefix%%(*}"  # drop scope: "feat(api)" -> "feat"

  # Strip prefix from rendered subject if present.
  if [[ "${subject}" == *":"* ]]; then
    rendered="${subject#*:}"
    rendered="${rendered# }"
  else
    rendered="${subject}"
  fi

  short_sha="${sha:0:7}"
  line="- ${rendered} ([${short_sha}](../../commit/${sha}))"

  case "${prefix}" in
    feat|feature|add)               echo "${line}" >> "$ADDED" ;;
    fix|bug|bugfix|hotfix)          echo "${line}" >> "$FIXED" ;;
    refactor|chore|style|perf|docs|ci|build|test)
                                    echo "${line}" >> "$CHANGED" ;;
    revert|remove|deprecate)        echo "${line}" >> "$REMOVED" ;;
    *)                              echo "${line}" >> "$CHANGED" ;;
  esac
done < <(git log ${RANGE} --no-merges --pretty=format:'%H%x09%s')

# Emit the section.
echo "## [${VERSION}] - ${TODAY}"
echo

emit_section() {
  local name="$1" file="$2"
  if [[ -s "$file" ]]; then
    echo "### ${name}"
    cat "$file"
    echo
  fi
}

emit_section "Added"   "$ADDED"
emit_section "Fixed"   "$FIXED"
emit_section "Changed" "$CHANGED"
emit_section "Removed" "$REMOVED"
