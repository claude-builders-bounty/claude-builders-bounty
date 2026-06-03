#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

if LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  RANGE="${LAST_TAG}..HEAD"
  RANGE_NOTE="Commits since ${LAST_TAG}."
else
  LAST_TAG=""
  RANGE="HEAD"
  RANGE_NOTE="No git tags found; using complete history."
fi

if ! git rev-list --count "$RANGE" >/dev/null 2>&1; then
  echo "Error: unable to read git history for range '${RANGE}'." >&2
  exit 1
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
declare -A SEEN_ENTRIES=()

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

strip_commit_prefix() {
  local subject="$1"
  subject="$(trim "$subject")"

  # Conventional commits: feat(scope)!: message -> message
  local conventional_re='^[A-Za-z]+(\([^)]+\))?!?:[[:space:]]*(.+)$'
  if [[ "$subject" =~ $conventional_re ]]; then
    subject="${BASH_REMATCH[2]}"
  fi

  # Non-conventional removal wording: remove legacy thing -> legacy thing
  if [[ "$subject" =~ ^[Rr]emove[[:space:]]+(.+)$ ]]; then
    subject="${BASH_REMATCH[1]}"
  elif [[ "$subject" =~ ^[Dd]elete[[:space:]]+(.+)$ ]]; then
    subject="${BASH_REMATCH[1]}"
  elif [[ "$subject" =~ ^[Dd]rop[[:space:]]+(.+)$ ]]; then
    subject="${BASH_REMATCH[1]}"
  fi

  printf '%s' "$(trim "$subject")"
}

category_for_subject() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|add:*|added:*|feature:*|feature\(*|*" add "*|add\ *) printf 'Added' ;;
    fix:*|fix\(*|bugfix:*|bugfix\(*|bug:*|bug\(*|repair:*|repair\ *) printf 'Fixed' ;;
    remove:*|removed:*|remove\ *|delete:*|delete\ *|drop:*|drop\ *) printf 'Removed' ;;
    refactor:*|refactor\(*|change:*|changed:*|docs:*|docs\(*|doc:*|doc\(*|perf:*|perf\(*|test:*|test\(*|ci:*|ci\(*|build:*|build\(*|style:*|style\(*|chore:*|chore\(*) printf 'Changed' ;;
    *) printf 'Changed' ;;
  esac
}

add_entry() {
  local category="$1"
  local entry="$2"
  local key="${category}:${entry}"

  [[ -n "${SEEN_ENTRIES[$key]:-}" ]] && return 0
  SEEN_ENTRIES[$key]=1

  case "$category" in
    Added) ADDED+=("$entry") ;;
    Fixed) FIXED+=("$entry") ;;
    Changed) CHANGED+=("$entry") ;;
    Removed) REMOVED+=("$entry") ;;
  esac
}

while IFS= read -r subject || [[ -n "$subject" ]]; do
  subject="$(trim "$subject")"
  [[ -z "$subject" ]] && continue
  [[ "$subject" =~ ^[Mm]erge[[:space:]] ]] && continue
  category="$(category_for_subject "$subject")"
  entry="$(strip_commit_prefix "$subject")"
  [[ -z "$entry" ]] && continue
  add_entry "$category" "$entry"
done < <(git log "$RANGE" --reverse --pretty=format:%s)

render_category() {
  local title="$1"
  shift
  local entries=("$@")
  if (( ${#entries[@]} > 0 )); then
    printf '### %s\n' "$title"
    local entry
    for entry in "${entries[@]}"; do
      printf -- '- %s\n' "$entry"
    done
    printf '\n'
  fi
}

TODAY="$(date +%F)"
TMP_FILE="$(mktemp)"
{
  printf '# Changelog\n\n'
  printf '## [Unreleased] - %s\n\n' "$TODAY"
  printf '_%s_\n\n' "$RANGE_NOTE"
  render_category "Added" "${ADDED[@]}"
  render_category "Fixed" "${FIXED[@]}"
  render_category "Changed" "${CHANGED[@]}"
  render_category "Removed" "${REMOVED[@]}"
  if (( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} == 0 )); then
    printf 'No changes found.\n\n'
  fi
} > "$TMP_FILE"

if [[ -f "$OUTPUT_FILE" ]]; then
  # Keep one title and prepend the new Unreleased section above the old releases.
  if grep -q '^# Changelog[[:space:]]*$' "$OUTPUT_FILE"; then
    awk 'BEGIN{seen=0} /^# Changelog[[:space:]]*$/ && seen==0 {seen=1; next} {print}' "$OUTPUT_FILE" >> "$TMP_FILE"
  else
    printf '\n' >> "$TMP_FILE"
    cat "$OUTPUT_FILE" >> "$TMP_FILE"
  fi
fi

mv "$TMP_FILE" "$OUTPUT_FILE"
echo "${RANGE_NOTE} Wrote ${OUTPUT_FILE}."
