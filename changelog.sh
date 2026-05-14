#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

LAST_TAG=""
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG="$(git describe --tags --abbrev=0)"
  RANGE="${LAST_TAG}..HEAD"
else
  RANGE="HEAD"
fi

if [[ -n "$LAST_TAG" ]]; then
  COMMITS="$(git log "$RANGE" --pretty=format:'%s' --no-merges)"
else
  COMMITS="$(git log --pretty=format:'%s' --no-merges)"
fi

if [[ -z "$COMMITS" ]]; then
  echo "error: no commits found for changelog range" >&2
  exit 1
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

add_entry() {
  local category="$1"
  local message="$2"

  case "$category" in
    added) ADDED+=("$message") ;;
    fixed) FIXED+=("$message") ;;
    changed) CHANGED+=("$message") ;;
    removed) REMOVED+=("$message") ;;
  esac
}

categorize_commit() {
  local subject="$1"
  local normalized
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feat\(*\):*|feature:*|add:*|added:*|*' add '*|*' adds '*|*' introduce '*|*' implements '*)
      add_entry added "$subject"
      ;;
    fix:*|fix\(*\):*|bugfix:*|hotfix:*|*' fix '*|*' fixes '*|*' repair '*|*' resolve '*)
      add_entry fixed "$subject"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|*' remove '*|*' removes '*|*' delete '*|*' deletes '*)
      add_entry removed "$subject"
      ;;
    refactor:*|refactor\(*\):*|change:*|changed:*|update:*|updated:*|docs:*|docs\(*\):*|chore:*|chore\(*\):*|style:*|style\(*\):*)
      add_entry changed "$subject"
      ;;
    *)
      add_entry changed "$subject"
      ;;
  esac
}

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  categorize_commit "$subject"
done <<< "$COMMITS"

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '## %s\n\n' "$title"
  if [[ "${#entries[@]}" -eq 0 ]]; then
    printf -- '- No changes.\n\n'
    return
  fi

  local entry
  for entry in "${entries[@]}"; do
    printf -- '- %s\n' "$entry"
  done
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated from git history on %s.\n\n' "$(date +%Y-%m-%d)"
  if [[ -n "$LAST_TAG" ]]; then
    printf 'Commit range: `%s..HEAD`.\n\n' "$LAST_TAG"
  else
    printf 'Commit range: all commits because no git tag was found.\n\n'
  fi
  write_section "Added" "${ADDED[@]+"${ADDED[@]}"}"
  write_section "Fixed" "${FIXED[@]+"${FIXED[@]}"}"
  write_section "Changed" "${CHANGED[@]+"${CHANGED[@]}"}"
  write_section "Removed" "${REMOVED[@]+"${REMOVED[@]}"}"
} > "$OUTPUT_FILE"

echo "Generated ${OUTPUT_FILE}"
