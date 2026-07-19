#!/usr/bin/env bash
set -euo pipefail

output_path="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: run this script inside a Git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  start_label="since ${latest_tag}"
else
  range="HEAD"
  start_label="from repository history"
fi

today="$(date +%Y-%m-%d)"
tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT
git log --format='%s' "$range" >"$tmp_file"

declare -a added=() fixed=() changed=() removed=()
while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  category="changed"
  case "$lower" in
    feat\(*|feat:*|feature\(*|feature:*|add\ *|added\ *|introduce\ *|implement\ *) category="added" ;;
    fix\(*|fix:*|bugfix\(*|bugfix:*|bug\ *|fix\ *|correct\ *|patch\ *) category="fixed" ;;
    remove\ *|removed\ *|delete\ *|deleted\ *|deprecate\ *|deprecates\ *|revert\ *) category="removed" ;;
    change\ *|changed\ *|refactor\ *|refactor\(*|refactor:*|perf\(*|perf:*|docs\ *|test\ *|tests\ *|build\ *|ci\ *|chore\ *) category="changed" ;;
    *security*|*vulnerabil*|*cve-*) category="fixed" ;;
    *remove*|*delet*|*deprecat*|*drop*) category="removed" ;;
    *add*|*support*|*introduc*|*implement*|*allow*) category="added" ;;
    *fix*|*correct*|*resolve*|*repair*|*patch*) category="fixed" ;;
  esac
  case "$category" in
    added) added+=("$subject") ;;
    fixed) fixed+=("$subject") ;;
    removed) removed+=("$subject") ;;
    changed) changed+=("$subject") ;;
  esac
done <"$tmp_file"

{
  printf '# Changelog\n\n'
  printf '## [Unreleased] - %s\n\n' "$today"
  for section in added fixed changed removed; do
    case "$section" in
      added) title="Added"; items_ref=added ;;
      fixed) title="Fixed"; items_ref=fixed ;;
      changed) title="Changed"; items_ref=changed ;;
      removed) title="Removed"; items_ref=removed ;;
    esac
    case "$items_ref" in
      added) item_count="${#added[@]}" ;;
      fixed) item_count="${#fixed[@]}" ;;
      changed) item_count="${#changed[@]}" ;;
      removed) item_count="${#removed[@]}" ;;
    esac
    [[ "$item_count" -eq 0 ]] && continue
    printf '### %s\n' "$title"
    case "$items_ref" in
      added) for item in "${added[@]}"; do printf '%s\n' "- $item"; done ;;
      fixed) for item in "${fixed[@]}"; do printf '%s\n' "- $item"; done ;;
      changed) for item in "${changed[@]}"; do printf '%s\n' "- $item"; done ;;
      removed) for item in "${removed[@]}"; do printf '%s\n' "- $item"; done ;;
    esac
    printf '\n'
  done
  if [[ ! -s "$tmp_file" ]]; then
    printf '_No commits found %s._\n' "$start_label"
  fi
} >"$output_path"

printf 'Generated %s (%s).\n' "$output_path" "$start_label"
