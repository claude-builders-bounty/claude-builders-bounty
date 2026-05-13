#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
TODAY="$(date +%Y-%m-%d)"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="$LAST_TAG..HEAD"
  RANGE_LABEL="since $LAST_TAG"
else
  RANGE="HEAD"
  RANGE_LABEL="from the full git history (no tags found)"
fi

COMMITS="$(git log "$RANGE" --no-merges --pretty=format:'%h%x09%s' 2>/dev/null || true)"

classify_commit() {
  local subject_lc="$1"

  case "$subject_lc" in
    feat:*|feature:*|add:*|added:*|*" add "*|*" adds "*|*" implement"*|*" introduce"*)
      printf 'Added'
      ;;
    fix:*|bugfix:*|hotfix:*|*" fix"*|*" fixes"*|*" bug"*|*" repair"*|*" resolve"*)
      printf 'Fixed'
      ;;
    remove:*|removed:*|delete:*|deleted:*|*" remove"*|*" delete"*|*" deprecat"*)
      printf 'Removed'
      ;;
    change:*|changed:*|refactor:*|perf:*|docs:*|style:*|test:*|build:*|ci:*|chore:*|*" update"*|*" change"*|*" refactor"*)
      printf 'Changed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

sanitize_subject() {
  local subject="$1"
  subject="${subject#feat: }"
  subject="${subject#feature: }"
  subject="${subject#fix: }"
  subject="${subject#bugfix: }"
  subject="${subject#hotfix: }"
  subject="${subject#change: }"
  subject="${subject#changed: }"
  subject="${subject#refactor: }"
  subject="${subject#perf: }"
  subject="${subject#docs: }"
  subject="${subject#style: }"
  subject="${subject#test: }"
  subject="${subject#build: }"
  subject="${subject#ci: }"
  subject="${subject#chore: }"
  subject="${subject#remove: }"
  subject="${subject#removed: }"
  subject="${subject#delete: }"
  subject="${subject#deleted: }"
  printf '%s' "$subject"
}

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

if [[ -n "$COMMITS" ]]; then
  while IFS=$'\t' read -r sha subject; do
    [[ -z "${sha:-}" || -z "${subject:-}" ]] && continue
    category="$(classify_commit "$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')")"
    line="$(sanitize_subject "$subject") ($sha)"
    case "$category" in
      Added) ADDED+=("$line") ;;
      Fixed) FIXED+=("$line") ;;
      Removed) REMOVED+=("$line") ;;
      *) CHANGED+=("$line") ;;
    esac
  done <<< "$COMMITS"
fi

write_section() {
  local title="$1"
  local trailing_blank="${2:-yes}"
  shift
  shift || true
  local entries=("$@")

  printf '### %s\n' "$title"
  if [[ ${#entries[@]} -eq 0 ]]; then
    printf -- '- No changes.\n'
    if [[ "$trailing_blank" == "yes" ]]; then
      printf '\n'
    fi
    return 0
  fi

  local entry
  for entry in "${entries[@]}"; do
    printf -- '- %s\n' "$entry"
  done
  if [[ "$trailing_blank" == "yes" ]]; then
    printf '\n'
  fi
  return 0
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes generated from git history.\n\n'
  printf '## Unreleased - %s\n\n' "$TODAY"
  printf '_Generated from commits %s._\n\n' "$RANGE_LABEL"
  write_section 'Added' yes "${ADDED[@]}"
  write_section 'Fixed' yes "${FIXED[@]}"
  write_section 'Changed' yes "${CHANGED[@]}"
  write_section 'Removed' no "${REMOVED[@]}"
} > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE using commits $RANGE_LABEL"
