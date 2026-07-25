#!/usr/bin/env bash

set -eo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf 'Error: run this command from inside a Git repository.\n' >&2
  exit 1
fi

added=()
fixed=()
changed=()
removed=()

if git rev-parse --verify HEAD >/dev/null 2>&1; then
  last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

  if [ -n "$last_tag" ]; then
    revision_range="refs/tags/${last_tag}..HEAD"
  else
    revision_range="HEAD"
  fi

  while IFS=$'\t' read -r short_hash subject; do
    [ -n "$subject" ] || continue

    normalized_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
    entry="- ${subject} (\`${short_hash}\`)"

    case "$normalized_subject" in
      feat* | add* | new*)
        added+=("$entry")
        ;;
      fix* | bugfix* | hotfix*)
        fixed+=("$entry")
        ;;
      remove* | delete* | breaking*)
        removed+=("$entry")
        ;;
      *)
        changed+=("$entry")
        ;;
    esac
  done < <(git log --no-merges --format='%h%x09%s' "$revision_range" --)
fi

write_section() {
  local title="$1"
  shift

  printf '### %s\n\n' "$title"
  if [ "$#" -eq 0 ]; then
    printf '%s\n' '- No changes.'
  else
    printf '%s\n' "$@"
  fi
  printf '\n'
}

temporary_file="$(mktemp ./CHANGELOG.md.tmp.XXXXXX)"
trap 'rm -f "$temporary_file"' EXIT

{
  printf '%s\n\n' '# Changelog'
  printf '%s\n\n' 'All notable changes to this project are documented in this file.'
  printf '## [Unreleased] - %s\n\n' "$(date +%Y-%m-%d)"
  write_section 'Added' "${added[@]}"
  write_section 'Fixed' "${fixed[@]}"
  write_section 'Changed' "${changed[@]}"
  write_section 'Removed' "${removed[@]}"
} >"$temporary_file"

mv "$temporary_file" CHANGELOG.md
trap - EXIT

if [ -n "${last_tag:-}" ]; then
  printf 'Generated CHANGELOG.md from commits after %s.\n' "$last_tag"
else
  printf '%s\n' 'Generated CHANGELOG.md from all commits (no tag found).'
fi
