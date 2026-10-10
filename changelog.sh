#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
#
#   bash changelog.sh          # run from inside any git repository
#
# Reads commits since the last git tag and groups them into
# Added / Fixed / Changed / Removed. Previously released sections of an
# existing CHANGELOG.md are preserved on re-runs.

set -euo pipefail

if [[ ! -d ".git" ]]; then
  echo "error: not a git repository — run from the repository root" >&2
  exit 1
fi

tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [[ -n "$tag" ]]; then
  # Commits since the last git tag.
  log=$(git log --pretty=format:'%s' "$tag..HEAD" 2>/dev/null || true)
else
  # Untagged repo: fall back to the entire history.
  log=$(git log --pretty=format:'%s' 2>/dev/null || true)
fi

added=()
fixed=()
changed=()
removed=()

while IFS= read -r line; do
  [[ -n "$line" ]] || continue
  # Categorize by the commit type. Handle conventional commits
  # ("feat(api)!: ..."), bare types ("fix: ...") and prose ("Fix the login").
  if [[ "$line" =~ ^([A-Za-z]+)(\([^\)]*\))?!?: ]]; then
    kw="${BASH_REMATCH[1],,}"
  else
    kw="${line%% *}"
    kw="${kw,,}"
  fi
  case "$kw" in
    feat|feature|add|added|new)            added+=("$line") ;;
    fix|fixed|bugfix|bug|patch)            fixed+=("$line") ;;
    remove|removed|deprecate|deprecated|breaking|revert) removed+=("$line") ;;
    *)                                     changed+=("$line") ;;
  esac
done <<< "$log"

write_section() {
  local title="$1"
  local -n items="$2"
  if [[ ${#items[@]} -eq 0 ]]; then
    return 0
  fi
  echo
  echo "### $title"
  printf '  - %s\n' "${items[@]}"
}

tmp=$(mktemp)
{
  echo "# Changelog"
  echo
  echo "All notable changes to this project will be documented in this file."
  echo
  echo "## [Unreleased]"
  write_section "Added" added
  write_section "Fixed" fixed
  write_section "Changed" changed
  write_section "Removed" removed

  if [[ -f CHANGELOG.md ]]; then
    prev=$(awk 'BEGIN{p=0} /^## / && $0 !~ /Unreleased/ {p=1} p' CHANGELOG.md)
    if [[ -n "$prev" ]]; then
      echo
      printf '%s\n' "$prev"
    fi
  fi
} > "$tmp"

mv "$tmp" CHANGELOG.md
chmod 0644 CHANGELOG.md 2>/dev/null || true
cat CHANGELOG.md