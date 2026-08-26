#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run this script inside a Git repository." >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  scope_label="Changes since ${last_tag}"
else
  range="HEAD"
  scope_label="Changes from repository history"
fi

categorize() {
  local subject="$1"
  local normalized
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    fix:*|fix\(*|fixed\ *|fix\ *|bugfix:*|bugfix\ *|patch:*|patch\ *|correct:*|correct\ *|resolve:*|resolve\ *|resolved\ *)
      printf '%s' "Fixed"
      ;;
    remove:*|remove\ *|removed\ *|delete:*|delete\ *|deleted\ *|drop:*|drop\ *|deprecated:*|deprecate:*|deprecate\ *)
      printf '%s' "Removed"
      ;;
    feat:*|feat\(*|feature:*|feature\ *|add:*|add\ *|added\ *|create:*|create\ *|created\ *|implement:*|implement\ *|implemented\ *|new:*|new\ *)
      printf '%s' "Added"
      ;;
    *)
      printf '%s' "Changed"
      ;;
  esac
}

strip_prefix() {
  local subject="$1"
  printf '%s' "$subject" | sed -E \
    -e 's/^(feat|fix|bugfix|patch|feature|add|remove|delete|drop|change|changed|update|updated|refactor|docs|doc|chore|perf|style|test|ci|build)(\([^)]*\))?!?:[[:space:]]*//' \
    -e 's/^[[:space:]]+//' \
    -e 's/[[:space:]]+$//'
}

added=""
fixed=""
changed=""
removed=""
commit_count=0

while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash:-}" ]] && continue
  commit_count=$((commit_count + 1))
  category="$(categorize "$subject")"
  clean_subject="$(strip_prefix "$subject")"
  [[ -z "$clean_subject" ]] && clean_subject="$subject"
  entry="- ${clean_subject} (${hash})"

  case "$category" in
    Added)   added+="${entry}"$'\n' ;;
    Fixed)   fixed+="${entry}"$'\n' ;;
    Changed) changed+="${entry}"$'\n' ;;
    Removed) removed+="${entry}"$'\n' ;;
  esac
done < <(git log "$range" --no-merges --pretty=tformat:'%h%x09%s')

{
  printf '# Changelog\n\n'
  printf '## %s - %s\n\n' "$scope_label" "$(date +%Y-%m-%d)"

  if [[ "$commit_count" -eq 0 ]]; then
    if [[ -n "$last_tag" ]]; then
      printf '_No changes since %s._\n' "$last_tag"
    else
      printf '_No commits found._\n'
    fi
    exit 0
  fi

  printf '### Added\n'
  if [[ -n "$added" ]]; then printf '%s' "$added"; else printf -- '- None\n'; fi
  printf '\n### Fixed\n'
  if [[ -n "$fixed" ]]; then printf '%s' "$fixed"; else printf -- '- None\n'; fi
  printf '\n### Changed\n'
  if [[ -n "$changed" ]]; then printf '%s' "$changed"; else printf -- '- None\n'; fi
  printf '\n### Removed\n'
  if [[ -n "$removed" ]]; then printf '%s' "$removed"; else printf -- '- None\n'; fi
} > "$OUTPUT_FILE"

echo "Wrote ${commit_count} commit(s) to ${OUTPUT_FILE}${last_tag:+ since ${last_tag}}."
