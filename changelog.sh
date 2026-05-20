#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
  RANGE_LABEL="since tag $LAST_TAG"
else
  RANGE="HEAD"
  RANGE_LABEL="for the full repository history (no tags found)"
fi

if ! COMMIT_COUNT="$(git rev-list --count "$RANGE" 2>/dev/null)"; then
  COMMIT_COUNT=0
fi

REMOTE_URL="$(git config --get remote.origin.url 2>/dev/null || true)"
GITHUB_URL=""
case "$REMOTE_URL" in
  git@github.com:*)
    GITHUB_URL="https://github.com/${REMOTE_URL#git@github.com:}"
    ;;
  ssh://git@github.com/*)
    GITHUB_URL="https://github.com/${REMOTE_URL#ssh://git@github.com/}"
    ;;
  https://github.com/*)
    GITHUB_URL="$REMOTE_URL"
    ;;
  http://github.com/*)
    GITHUB_URL="https://${REMOTE_URL#http://}"
    ;;
esac
GITHUB_URL="${GITHUB_URL%.git}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

for CATEGORY in Added Fixed Changed Removed; do
  : > "$TMP_DIR/$CATEGORY"
done

categorize_commit() {
  local subject_lower="$1"

  case "$subject_lower" in
    remove*|removed*|delete*|deleted*|drop*|dropped*|deprecat*)
      printf 'Removed'
      ;;
    fix*|fixed*|bug*|bugfix*|hotfix*|repair*|resolve*)
      printf 'Fixed'
      ;;
    feat*|feature*|add*|added*|implement*|create*|introduce*)
      printf 'Added'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

format_commit_reference() {
  local hash="$1"
  local short_hash="${hash:0:7}"

  if [ -n "$GITHUB_URL" ]; then
    printf '([`%s`](%s/commit/%s))' "$short_hash" "$GITHUB_URL" "$hash"
  else
    printf '(`%s`)' "$short_hash"
  fi
}

while IFS=$'\037' read -r HASH SUBJECT; do
  [ -n "${HASH:-}" ] || continue

  SUBJECT_LOWER="$(printf '%s' "$SUBJECT" | tr '[:upper:]' '[:lower:]')"
  CATEGORY="$(categorize_commit "$SUBJECT_LOWER")"
  CLEAN_SUBJECT="$(printf '%s' "$SUBJECT" | sed -E 's/^[[:alpha:]]+(\([^)]+\))?!?:[[:space:]]*//')"
  [ -n "$CLEAN_SUBJECT" ] || CLEAN_SUBJECT="$SUBJECT"

  printf -- '- %s %s\n' "$CLEAN_SUBJECT" "$(format_commit_reference "$HASH")" >> "$TMP_DIR/$CATEGORY"
done < <(git log --reverse --format='%H%x1f%s' "$RANGE" 2>/dev/null || true)

TODAY="$(date +%Y-%m-%d)"

{
  printf '# Changelog\n\n'
  printf 'Generated on %s from git commits %s.\n\n' "$TODAY" "$RANGE_LABEL"
  printf '## [Unreleased] - %s\n' "$TODAY"

  for CATEGORY in Added Fixed Changed Removed; do
    printf '\n### %s\n' "$CATEGORY"
    if [ -s "$TMP_DIR/$CATEGORY" ]; then
      cat "$TMP_DIR/$CATEGORY"
    else
      printf -- '- No %s changes.\n' "$CATEGORY"
    fi
  done

  if [ -n "$LAST_TAG" ]; then
    printf '\n_Last tag scanned from: `%s`._\n' "$LAST_TAG"
  else
    printf '\n_No git tags were found, so the full commit history was scanned._\n'
  fi
} > "$OUTPUT_FILE"

printf 'Generated %s with %s commit(s) %s.\n' "$OUTPUT_FILE" "$COMMIT_COUNT" "$RANGE_LABEL"
