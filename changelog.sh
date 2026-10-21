#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history (since last tag).
# Usage: bash changelog.sh [output_path]
set -euo pipefail

OUT="${1:-CHANGELOG.md}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "${LAST_TAG}" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  RANGE_LABEL="full history (no tags)"
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

# shellcheck disable=SC2086
git log ${RANGE} --pretty=format:'%h%x09%s' --no-merges >"$TMP" 2>/dev/null || true

emit_section() {
  local title="$1"
  local file="$2"
  echo "## ${title}"
  echo
  if [[ ! -s "$file" ]]; then
    echo "_None in this range._"
  else
    cat "$file"
  fi
  echo
}

ADDED="$(mktemp)"; FIXED="$(mktemp)"; CHANGED="$(mktemp)"; REMOVED="$(mktemp)"
trap 'rm -f "$TMP" "$ADDED" "$FIXED" "$CHANGED" "$REMOVED"' EXIT

while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash:-}" ]] && continue
  low="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  line="- ${subject} (${hash})"
  if [[ "$low" =~ ^(feat|feature|add)(\(|:|[[:space:]]) ]] || [[ "$low" =~ (^|[[:space:]])added([[:space:]]|$) ]]; then
    printf '%s\n' "$line" >>"$ADDED"
  elif [[ "$low" =~ ^(fix|bugfix|hotfix)(\(|:|[[:space:]]) ]] || [[ "$low" =~ ^(fixed?|fixes)(\(|:|[[:space:]]) ]]; then
    printf '%s\n' "$line" >>"$FIXED"
  elif [[ "$low" =~ ^(remove|delete|drop)(\(|:|[[:space:]]) ]] || [[ "$low" =~ ^(removed|deleted|dropped)(\(|:|[[:space:]]) ]]; then
    printf '%s\n' "$line" >>"$REMOVED"
  elif [[ "$low" =~ ^(change|changed|refactor|perf|chore|docs|style|build|ci)(\(|:|[[:space:]]) ]]; then
    printf '%s\n' "$line" >>"$CHANGED"
  elif [[ "$low" =~ \b(add|added|introduce|new)\b ]]; then
    printf '%s\n' "$line" >>"$ADDED"
  elif [[ "$low" =~ \b(fix|fixed|bug|crash|error)\b ]]; then
    printf '%s\n' "$line" >>"$FIXED"
  elif [[ "$low" =~ \b(remove|removed|delete|drop)\b ]]; then
    printf '%s\n' "$line" >>"$REMOVED"
  else
    printf '%s\n' "$line" >>"$CHANGED"
  fi
done <"$TMP"

{
  echo "# Changelog"
  echo
  echo "Generated ${RANGE_LABEL}."
  echo
  emit_section "Added" "$ADDED"
  emit_section "Fixed" "$FIXED"
  emit_section "Changed" "$CHANGED"
  emit_section "Removed" "$REMOVED"
} >"$OUT"

echo "Wrote ${OUT} (${RANGE_LABEL})"
