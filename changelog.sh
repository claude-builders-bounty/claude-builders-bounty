#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: run this script inside a Git repository" >&2
  exit 1
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "error: repository has no commits" >&2
  exit 1
fi

LATEST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LATEST_TAG" ]]; then
  RANGE="${LATEST_TAG}..HEAD"
  SOURCE_LABEL="commits since ${LATEST_TAG}"
else
  RANGE="HEAD"
  SOURCE_LABEL="all commits (no git tags found)"
fi

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/changelog.XXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

ADDED_FILE="$WORK_DIR/added"
FIXED_FILE="$WORK_DIR/fixed"
CHANGED_FILE="$WORK_DIR/changed"
REMOVED_FILE="$WORK_DIR/removed"
: > "$ADDED_FILE"
: > "$FIXED_FILE"
: > "$CHANGED_FILE"
: > "$REMOVED_FILE"

while IFS=$'\t' read -r sha subject || [[ -n "${sha:-}" ]]; do
  [[ -z "${sha:-}" ]] && continue

  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  destination="$CHANGED_FILE"

  case "$normalized" in
    feat:*|feat\(*|add:*|add\ *|added\ *|new:*|new\ *|create:*|create\ *)
      destination="$ADDED_FILE"
      ;;
    fix:*|fix\(*|fix\ *|fixed\ *|bugfix:*|bugfix\ *|hotfix:*|hotfix\ *|repair:*|repair\ *)
      destination="$FIXED_FILE"
      ;;
    remove:*|remove\ *|removed\ *|delete:*|delete\ *|deleted\ *|drop:*|drop\ *|deprecate:*|deprecate\ *)
      destination="$REMOVED_FILE"
      ;;
  esac

  printf -- '- %s (`%s`)\n' "$subject" "$sha" >> "$destination"
done < <(git log "$RANGE" --no-merges --reverse --pretty=format:'%h%x09%s')

render_section() {
  local title="$1"
  local file="$2"

  printf '### %s\n' "$title"
  if [[ -s "$file" ]]; then
    cat "$file"
  else
    printf '%s\n' '- _No entries_'
  fi
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated from %s.\n\n' "$SOURCE_LABEL"
  printf '## Unreleased\n\n'
  render_section "Added" "$ADDED_FILE"
  render_section "Fixed" "$FIXED_FILE"
  render_section "Changed" "$CHANGED_FILE"
  render_section "Removed" "$REMOVED_FILE"
} > "$OUTPUT_FILE"

COMMIT_COUNT="$(
  cat "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE" | wc -l | tr -d ' '
)"

echo "Wrote $OUTPUT_FILE from $COMMIT_COUNT commit(s)."
