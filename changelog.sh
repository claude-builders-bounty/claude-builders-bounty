#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="${CHANGELOG_FILE:-CHANGELOG.md}"
TITLE="${CHANGELOG_TITLE:-Changelog}"
RANGE="${1:-}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

if [[ -z "$RANGE" ]]; then
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
  if [[ -n "$LAST_TAG" ]]; then
    RANGE="$LAST_TAG..HEAD"
    RANGE_LABEL="since $LAST_TAG"
  else
    RANGE="HEAD"
    RANGE_LABEL="from repository history"
  fi
else
  RANGE_LABEL="for $RANGE"
fi

TMP_COMMITS="$(mktemp)"
trap 'rm -f "$TMP_COMMITS"' EXIT

git log "$RANGE" --no-merges --pretty=format:'%s' > "$TMP_COMMITS"

section_items() {
  local regex="$1"
  local fallback_regex="$2"
  local seen=0
  while IFS= read -r subject || [[ -n "$subject" ]]; do
    [[ -z "$subject" ]] && continue
    if [[ "$subject" =~ $regex ]] || { [[ -n "$fallback_regex" ]] && [[ "$subject" =~ $fallback_regex ]]; }; then
      clean_subject "$subject"
      seen=1
    fi
  done < "$TMP_COMMITS"
  if [[ "$seen" -eq 0 ]]; then
    echo "- None"
  fi
}

clean_subject() {
  local subject="$1"
  subject="${subject#feat: }"; subject="${subject#feat!: }"; subject="${subject#feature: }"
  subject="${subject#fix: }"; subject="${subject#bugfix: }"
  subject="${subject#refactor: }"; subject="${subject#perf: }"; subject="${subject#chore: }"
  subject="${subject#docs: }"; subject="${subject#test: }"; subject="${subject#ci: }"
  subject="${subject#remove: }"; subject="${subject#removed: }"; subject="${subject#delete: }"
  printf -- '- %s\n' "$subject"
}

TODAY="$(date -u +%Y-%m-%d)"
{
  echo "# $TITLE"
  echo
  echo "Generated on $TODAY $RANGE_LABEL."
  echo
  echo "## Unreleased"
  echo
  echo "### Added"
  section_items '^(feat|feature)(\([^)]*\))?!?:' '^(add|added|create|created|introduce|introduced)([[:space:]:]|$)'
  echo
  echo "### Fixed"
  section_items '^(fix|bugfix)(\([^)]*\))?!?:' '^(fix|fixed|repair|patched|resolve|resolved)([[:space:]:]|$)'
  echo
  echo "### Changed"
  section_items '^(change|changed|refactor|perf|chore|docs|test|ci)(\([^)]*\))?!?:' '^(update|updated|improve|improved|refactor|rename|renamed)([[:space:]:]|$)'
  echo
  echo "### Removed"
  section_items '^(remove|removed|delete|deleted)(\([^)]*\))?!?:' '^(remove|removed|delete|deleted|drop|dropped)([[:space:]:]|$)'
} > "$OUT_FILE"

echo "Wrote $OUT_FILE using commits $RANGE_LABEL"
