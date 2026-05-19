#!/usr/bin/env bash
set -euo pipefail

out="${1:-CHANGELOG.md}"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
cd "$repo_root"

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$last_tag" ]; then
  range="$last_tag..HEAD"
  since="since $last_tag"
else
  range="HEAD"
  since="from repository start"
fi

version="Unreleased"
date_utc="$(date -u +%Y-%m-%d)"

commits="$(git log --no-merges --pretty=format:'%s' "$range" 2>/dev/null || true)"

bucket() {
  local name="$1" pattern="$2"
  printf '### %s\n' "$name"
  local lines
  lines="$(printf '%s\n' "$commits" | grep -Eis "$pattern" || true)"
  if [ -z "$lines" ]; then
    printf -- '- None\n\n'
  else
    printf '%s\n' "$lines" | sed -E 's/^[[:space:]]+//; s/^/- /'
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf '## %s - %s\n\n' "$version" "$date_utc"
  printf '_Generated from git history %s._\n\n' "$since"
  bucket 'Added' '^(feat|feature|add|added)(\(.+\))?:|add(ed)? '
  bucket 'Fixed' '^(fix|bugfix|hotfix|repair)(\(.+\))?:|fix(ed|es)? |bug'
  bucket 'Changed' '^(change|changed|refactor|perf|docs|style|test|chore|build|ci)(\(.+\))?:|update(d)? |improve(d)? |refactor'
  bucket 'Removed' '^(remove|removed|delete|deleted|drop|dropped)(\(.+\))?:|remove(d)? |delete(d)? |drop(ped)?'
} > "$out"

printf 'Wrote %s using commits %s\n' "$out" "$since"
