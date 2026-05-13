#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="${1:-CHANGELOG.md}"
RANGE="${CHANGELOG_RANGE:-}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

if [[ -z "$RANGE" ]]; then
  if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    RANGE="$(git describe --tags --abbrev=0)..HEAD"
  else
    RANGE="HEAD"
  fi
fi

collect() {
  local pattern="$1"
  git log "$RANGE" --no-merges --pretty=format:'%s' 2>/dev/null \
    | grep -Ei "$pattern" \
    | sed -E 's/^[a-z]+(\([^)]*\))?!?:[[:space:]]*//I; s/^/- /' \
    | sort -u || true
}

added="$(collect '^(feat|feature|add)(\(.+\))?!?:|^add(ed)?[[:space:]]')"
fixed="$(collect '^(fix|bugfix|hotfix)(\(.+\))?!?:|^fix(ed)?[[:space:]]')"
changed="$(collect '^(change|refactor|perf|docs|style|test|chore)(\(.+\))?!?:|^(change|update|improve|refactor)')"
removed="$(collect '^(remove|delete|drop)(\(.+\))?!?:|^(remove|delete|drop)[[:space:]]')"

write_section() {
  local title="$1"
  local body="$2"
  printf '## %s\n' "$title"
  if [[ -n "$body" ]]; then
    printf '%s\n\n' "$body"
  else
    printf -- '- No changes.\n\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf 'Generated from git history. Range: `%s`\n\n' "$RANGE"
  write_section "Added" "$added"
  write_section "Fixed" "$fixed"
  write_section "Changed" "$changed"
  write_section "Removed" "$removed"
} > "$OUT_FILE"

printf 'Wrote %s\n' "$OUT_FILE"
