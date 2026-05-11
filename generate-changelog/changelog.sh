#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "error: changelog.sh must run inside a git repository" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="$LAST_TAG..HEAD"
  SINCE_LABEL="since $LAST_TAG"
else
  RANGE="HEAD"
  SINCE_LABEL="from first commit"
fi

VERSION="Unreleased"
TODAY="$(date +%Y-%m-%d)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

git log "$RANGE" --no-merges --pretty=format:'%s%x09%h%x09%an' > "$TMP" || true

bucket_for_subject() {
  local subject
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$subject" in
    feat:*|feature:*|add:*|added:*|create:*|implement:*|initial*|new:*) echo "Added" ;;
    fix:*|bugfix:*|hotfix:*|repair:*|resolve:*|correct:*|patch:*) echo "Fixed" ;;
    change:*|changed:*|update:*|refactor:*|perf:*|improve:*|enhance:*|docs:*|doc:*|style:*|test:*|build:*|ci:*|chore:*) echo "Changed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*) echo "Removed" ;;
    *) echo "Changed" ;;
  esac
}

make_line() {
  local subject="$1" sha="$2" author="$3"
  # Strip common conventional-commit prefixes after categorizing.
  local clean="$subject"
  clean="$(printf '%s' "$clean" | sed -E 's/^(feat|feature|fix|bugfix|hotfix|docs|doc|style|refactor|perf|test|build|ci|chore|add|added|create|implement|update|change|changed|remove|removed|delete|deleted)(\([^)]*\))?!?:[[:space:]]*//I')"
  printf -- '- %s (`%s`, %s)\n' "$clean" "$sha" "$author"
}

declare -a ADDED=() FIXED=() CHANGED=() REMOVED=()
while IFS=$'\t' read -r subject sha author || [[ -n "${subject:-}" ]]; do
  [[ -z "${subject:-}" ]] && continue
  line="$(make_line "$subject" "$sha" "$author")"
  case "$(bucket_for_subject "$subject")" in
    Added) ADDED+=("$line") ;;
    Fixed) FIXED+=("$line") ;;
    Removed) REMOVED+=("$line") ;;
    *) CHANGED+=("$line") ;;
  esac
done < "$TMP"

print_section() {
  local title="$1"
  shift
  echo "### $title"
  if [[ "$#" -eq 0 ]]; then
    echo "- No entries."
  else
    printf '%s' "$@"
  fi
  echo
}

{
  echo "# Changelog"
  echo
  echo "All notable changes generated from git history."
  echo
  echo "## [$VERSION] - $TODAY"
  echo
  echo "Source range: $SINCE_LABEL"
  echo
  set +u
  print_section "Added" "${ADDED[@]}"
  print_section "Fixed" "${FIXED[@]}"
  print_section "Changed" "${CHANGED[@]}"
  print_section "Removed" "${REMOVED[@]}"
  set -u
} > "$OUTPUT_FILE"

echo "Generated $OUTPUT_FILE using commits $SINCE_LABEL"
