#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
TODAY="$(date +%Y-%m-%d)"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

if git remote >/dev/null 2>&1 && [ -n "$(git remote | head -n 1)" ]; then
  git fetch --tags --quiet >/dev/null 2>&1 || true
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="$LAST_TAG..HEAD"
  RANGE_LABEL="since $LAST_TAG"
else
  RANGE="HEAD"
  RANGE_LABEL="from repository history"
fi

mapfile -t COMMITS < <(git log "$RANGE" --no-merges --pretty=format:'%s||%h' 2>/dev/null || true)

clean_subject() {
  local subject="$1"
  subject="${subject#feat: }"; subject="${subject#feat!: }"
  subject="${subject#fix: }"; subject="${subject#fix!: }"
  subject="${subject#chore: }"; subject="${subject#docs: }"
  subject="${subject#refactor: }"; subject="${subject#perf: }"
  subject="${subject#test: }"; subject="${subject#style: }"
  subject="${subject#build: }"; subject="${subject#ci: }"
  subject="${subject#remove: }"; subject="${subject#removed: }"
  subject="${subject#delete: }"; subject="${subject#deleted: }"
  printf '%s' "$subject"
}

category_for() {
  local subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$subject" in
    feat:*|feat\!*|add:*|added:*|new:*|implement:*|initial:*|create:*) echo "Added" ;;
    fix:*|fix\!*|bug:*|bugfix:*|repair:*|resolve:*|hotfix:*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|deprecated:*|drop:*) echo "Removed" ;;
    *) echo "Changed" ;;
  esac
}

declare -a ADDED FIXED CHANGED REMOVED
for entry in "${COMMITS[@]}"; do
  subject="${entry%%||*}"
  hash="${entry##*||}"
  [ -n "$subject" ] || continue
  category="$(category_for "$subject")"
  line="- $(clean_subject "$subject") (${hash})"
  case "$category" in
    Added) ADDED+=("$line") ;;
    Fixed) FIXED+=("$line") ;;
    Removed) REMOVED+=("$line") ;;
    *) CHANGED+=("$line") ;;
  esac
done

write_section() {
  local title="$1"
  shift
  printf '### %s\n' "$title"
  if [ "$#" -eq 0 ]; then
    printf -- '- None\n\n'
  else
    printf '%s\n' "$@"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes are grouped from git history.\n\n'
  printf '## Unreleased - %s\n\n' "$TODAY"
  printf '_Generated from commits %s._\n\n' "$RANGE_LABEL"
  write_section "Added" "${ADDED[@]}"
  write_section "Fixed" "${FIXED[@]}"
  write_section "Changed" "${CHANGED[@]}"
  write_section "Removed" "${REMOVED[@]}"
} > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE using commits $RANGE_LABEL"
