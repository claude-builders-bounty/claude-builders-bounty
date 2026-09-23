#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
}
cd "$repo_root"

if last_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range="$last_tag..HEAD"
  since_label="since $last_tag"
else
  range="HEAD"
  since_label="for all commits"
fi

mapfile -t commits < <(git log --no-merges --date=short --pretty=format:'%h%x09%ad%x09%s' "$range")

declare -a added fixed changed removed

categorize() {
  local subject_lc="$1"
  case "$subject_lc" in
    feat:*|feature:*|add:*|added:*|*" add "*|add\ *|*" introduce"*|introduce\ *) echo "Added" ;;
    fix:*|fixed:*|bugfix:*|hotfix:*|*" fix "*|fix\ *|*" repair"*|repair\ *) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|*" remove "*|remove\ *|*" delete "*|delete\ *) echo "Removed" ;;
    change:*|changed:*|refactor:*|update:*|updated:*|docs:*|test:*|chore:*|*" update "*|update\ *) echo "Changed" ;;
    *) echo "Changed" ;;
  esac
}

append_item() {
  local category="$1" item="$2"
  case "$category" in
    Added) added+=("$item") ;;
    Fixed) fixed+=("$item") ;;
    Removed) removed+=("$item") ;;
    *) changed+=("$item") ;;
  esac
}

for row in "${commits[@]}"; do
  IFS=$'\t' read -r hash date subject <<< "$row"
  category="$(categorize "$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')")"
  append_item "$category" "- $subject ($hash, $date)"
done

{
  echo "# Changelog"
  echo
  echo "Generated from git history $since_label on $(date -u +%Y-%m-%d)."
  echo
  for section in Added Fixed Changed Removed; do
    echo "## $section"
    echo
    case "$section" in
      Added) items=("${added[@]:-}") ;;
      Fixed) items=("${fixed[@]:-}") ;;
      Changed) items=("${changed[@]:-}") ;;
      Removed) items=("${removed[@]:-}") ;;
    esac
    if [ "${#items[@]}" -eq 0 ] || [ -z "${items[0]:-}" ]; then
      echo "- None"
    else
      printf '%s\n' "${items[@]}"
    fi
    echo
  done
} > "$output_file"

echo "Wrote $output_file from ${#commits[@]} commit(s) $since_label."
