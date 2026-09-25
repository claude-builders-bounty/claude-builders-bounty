#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history since the last tag.
#
# Usage:
#   bash changelog.sh [range] [output_file]
#
#   range        Optional git revision range (e.g. "v1.0.0..HEAD").
#                Defaults to "<last-tag>..HEAD", or the full history if no tag exists.
#   output_file  Optional path to write the changelog to. Defaults to "CHANGELOG.md".

set -euo pipefail

RANGE="${1:-}"
OUTPUT_FILE="${2:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

LAST_TAG=""
if [ -z "$RANGE" ]; then
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
  else
    RANGE="HEAD"
  fi
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS=$'\x1f' read -r hash subject; do
  [ -z "$hash" ] && continue

  prefix="$(printf '%s' "$subject" | sed -E 's/^([A-Za-z]+)(\(.+\))?!?:.*/\1/' | tr '[:upper:]' '[:lower:]')"
  entry="- ${subject} (${hash})"

  case "$prefix" in
    feat|add)
      ADDED+=("$entry")
      ;;
    fix|bug)
      FIXED+=("$entry")
      ;;
    remove|delete|revert)
      REMOVED+=("$entry")
      ;;
    refactor|change|update|perf|style|chore|docs|test|build|ci)
      CHANGED+=("$entry")
      ;;
    *)
      CHANGED+=("$entry")
      ;;
  esac
done < <(git log "$RANGE" --no-merges --pretty=format:'%h%x1f%s')

DATE="$(date +%Y-%m-%d)"
HEADER_LABEL="${LAST_TAG:-Unreleased}"

{
  echo "## [${HEADER_LABEL}] - ${DATE}"
  echo ""

  if [ "${#ADDED[@]}" -gt 0 ]; then
    echo "### Added"
    printf '%s\n' "${ADDED[@]}"
    echo ""
  fi

  if [ "${#FIXED[@]}" -gt 0 ]; then
    echo "### Fixed"
    printf '%s\n' "${FIXED[@]}"
    echo ""
  fi

  if [ "${#CHANGED[@]}" -gt 0 ]; then
    echo "### Changed"
    printf '%s\n' "${CHANGED[@]}"
    echo ""
  fi

  if [ "${#REMOVED[@]}" -gt 0 ]; then
    echo "### Removed"
    printf '%s\n' "${REMOVED[@]}"
    echo ""
  fi
} > /tmp/changelog_new_section.$$

if [ -f "$OUTPUT_FILE" ]; then
  {
    if head -n1 "$OUTPUT_FILE" | grep -q '^# Changelog'; then
      head -n1 "$OUTPUT_FILE"
      echo ""
      cat /tmp/changelog_new_section.$$
      tail -n +2 "$OUTPUT_FILE"
    else
      echo "# Changelog"
      echo ""
      cat /tmp/changelog_new_section.$$
      cat "$OUTPUT_FILE"
    fi
  } > /tmp/changelog_full.$$
  mv /tmp/changelog_full.$$ "$OUTPUT_FILE"
else
  {
    echo "# Changelog"
    echo ""
    cat /tmp/changelog_new_section.$$
  } > "$OUTPUT_FILE"
fi

rm -f /tmp/changelog_new_section.$$

echo "Wrote changelog section for range '${RANGE}' to ${OUTPUT_FILE}"
