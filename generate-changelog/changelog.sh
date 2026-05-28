#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required to generate a changelog." >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: this script must be run inside a git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [ -n "$latest_tag" ]; then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range="HEAD"
  since_label="from the full git history"
fi

commits="$(git log "$range" --pretty=format:'%s' --no-merges 2>/dev/null || true)"

release_date="$(date +%Y-%m-%d)"
temp_file="$(mktemp)"

write_section() {
  local title="$1"
  local pattern="$2"
  local fallback="$3"
  local matches

  matches="$(printf '%s\n' "$commits" | grep -E -i "$pattern" || true)"

  {
    printf '### %s\n\n' "$title"
    if [ -n "$matches" ]; then
      printf '%s\n' "$matches" | sed -E 's/^[[:space:]]*[-*]?[[:space:]]*/- /'
    else
      printf -- '- %s\n' "$fallback"
    fi
    printf '\n'
  } >> "$temp_file"
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$release_date"
  printf '_Generated %s._\n\n' "$since_label"
} > "$temp_file"

if [ -z "$commits" ]; then
  {
    printf '### Added\n\n'
    printf -- '- No commits found for this release range.\n\n'
    printf '### Fixed\n\n'
    printf -- '- No fixes found.\n\n'
    printf '### Changed\n\n'
    printf -- '- No changes found.\n\n'
    printf '### Removed\n\n'
    printf -- '- No removals found.\n'
  } >> "$temp_file"
else
  write_section "Added" '^(add|added|feat|feature)(\(.+\))?:|^add |^added |^new ' "No new additions found."
  write_section "Fixed" '^(fix|fixed|bugfix|hotfix)(\(.+\))?:|^fix |^fixed |^bug ' "No fixes found."
  write_section "Changed" '^(change|changed|chore|refactor|perf|docs|style|test|build|ci)(\(.+\))?:|^update |^updated |^improve |^improved ' "No general changes found."
  write_section "Removed" '^(remove|removed|delete|deleted|deprecate|deprecated)(\(.+\))?:|^remove |^removed |^delete |^deleted ' "No removals found."
fi

mv "$temp_file" "$output_file"
echo "Generated ${output_file}"
