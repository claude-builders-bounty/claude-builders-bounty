#!/usr/bin/env bash
set -euo pipefail

# Generate a Keep a Changelog-style CHANGELOG.md from commits since the last tag.
# Usage: bash scripts/generate_changelog.sh [from_ref] [to_ref]

FROM_REF="${1:-}"
TO_REF="${2:-HEAD}"
OUT_FILE="CHANGELOG.md"

if [[ -z "$FROM_REF" ]]; then
  FROM_REF="$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)"
fi

range="$FROM_REF..$TO_REF"
today="$(date +%Y-%m-%d)"

collect() {
  local pattern="$1"
  git log "$range" --reverse --pretty=format:'%s' --grep="$pattern" -E |
    sed -E "s/^(${pattern})!?(:|\([^)]+\):)[[:space:]]*//I" |
    sed '/^[[:space:]]*$/d' |
    sed 's/^/- /'
}

added="$(collect 'feat')"
fixed="$(collect 'fix')"
changed="$(git log "$range" --reverse --pretty=format:'%s' --grep='^(refactor|perf|build|ci|chore)' -E |
  sed -E 's/^(refactor|perf|build|ci|chore)!?(\([^)]+\))?:[[:space:]]*//I' |
  sed '/^[[:space:]]*$/d' |
  sed 's/^/- /')"
removed="$(git log "$range" --reverse --pretty=format:'%s' --grep='^(remove|removed|delete|deleted)' -E |
  sed -E 's/^(remove|removed|delete|deleted)!?(\([^)]+\))?:[[:space:]]*//I' |
  sed '/^[[:space:]]*$/d' |
  sed 's/^/- /')"

{
  echo '# Changelog'
  echo
  echo 'All notable changes to this project will be documented in this file.'
  echo
  echo "## [Unreleased] - $today"
  echo
  echo '### Added'
  [[ -n "$added" ]] && echo "$added" || echo '- No added changes found.'
  echo
  echo '### Fixed'
  [[ -n "$fixed" ]] && echo "$fixed" || echo '- No fixes found.'
  echo
  echo '### Changed'
  [[ -n "$changed" ]] && echo "$changed" || echo '- No changed items found.'
  echo
  echo '### Removed'
  [[ -n "$removed" ]] && echo "$removed" || echo '- No removed items found.'
} > "$OUT_FILE"

printf 'Generated %s from %s\n' "$OUT_FILE" "$range"
