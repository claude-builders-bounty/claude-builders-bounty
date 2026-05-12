#!/usr/bin/env bash
set -euo pipefail

# Generate a Keep a Changelog-style CHANGELOG.md from git commits since the last tag.
# Usage: ./changelog.sh [output-file]

OUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

latest_tag=""
if latest_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range="HEAD"
  since_label="from project history"
fi

if ! git rev-list --count "$range" >/dev/null 2>&1; then
  echo "Error: unable to read commits for range '${range}'." >&2
  exit 1
fi

version="Unreleased"
date_utc="$(date -u +%Y-%m-%d)"

added=()
fixed=()
changed=()
removed=()

clean_subject() {
  local subject="$1"
  subject="${subject#*: }"
  subject="${subject#- }"
  printf '%s' "$subject"
}

add_entry() {
  local category="$1"
  local subject="$2"
  local sha="$3"
  local entry="$(clean_subject "$subject") (${sha})"
  case "$category" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    changed) changed+=("$entry") ;;
    removed) removed+=("$entry") ;;
  esac
}

while IFS=$'\t' read -r sha subject || [ -n "${sha:-}" ]; do
  [ -n "${sha:-}" ] || continue
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    feat:*|feat\(*|add:*|added:*|new:*) add_entry added "$subject" "$sha" ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|security:*) add_entry fixed "$subject" "$sha" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*) add_entry removed "$subject" "$sha" ;;
    change:*|changed:*|update:*|updated:*|refactor:*|perf:*|docs:*|style:*|test:*|chore:*|ci:*|build:*) add_entry changed "$subject" "$sha" ;;
    *) add_entry changed "$subject" "$sha" ;;
  esac
done < <(git log --reverse --pretty=format:'%h%x09%s' "$range")

write_section() {
  local title="$1"
  shift
  local -n entries_ref="$1"
  printf '\n### %s\n' "$title"
  if [ "${#entries_ref[@]}" -eq 0 ]; then
    printf -- '- None\n'
  else
    for entry in "${entries_ref[@]}"; do
      printf -- '- %s\n' "$entry"
    done
  fi
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git history.\n\n'
  printf '## [%s] - %s\n\n' "$version" "$date_utc"
  printf '_Generated from commits %s._\n' "$since_label"
  write_section 'Added' added
  write_section 'Fixed' fixed
  write_section 'Changed' changed
  write_section 'Removed' removed
} > "$OUT_FILE"

printf 'Wrote %s using commits %s.\n' "$OUT_FILE" "$since_label"
