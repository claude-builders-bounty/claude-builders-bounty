#!/usr/bin/env bash
set -euo pipefail

output=${1:-CHANGELOG.md}
today=$(date -u +%F)

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: run changelog.sh inside a git repository" >&2
  exit 1
fi

last_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [[ -n "$last_tag" ]]; then
  range="$last_tag..HEAD"
else
  root=$(git rev-list --max-parents=0 --reverse HEAD | head -n 1)
  range="$root..HEAD"
fi

declare -a added=() fixed=() changed=() removed=()
remote_url=$(git remote get-url origin 2>/dev/null || true)
remote_url=${remote_url%.git}
while IFS=$'\t' read -r hash subject; do
  [[ -z "$hash" ]] && continue
  short=${hash:0:7}
  line="$subject ([${short}]($remote_url/commit/$hash))"
  normalized=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')
  case "$normalized" in
    feat:*|feature:*|add:*|new:*|create:*) added+=("- $line") ;;
    fix:*|bugfix:*|hotfix:*|bug:*) fixed+=("- $line") ;;
    remove:*|removed:*|delete:*|drop:*) removed+=("- $line") ;;
    *) changed+=("- $line") ;;
  esac
done < <(git log --no-merges --format='%H%x09%s' "$range")

{
  echo "# Changelog"
  echo
  echo "All notable changes to this project are documented here."
  echo
  echo "## [Unreleased] - $today"
  echo
  for section in added fixed changed removed; do
    declare -n entries="$section"
    [[ ${#entries[@]} -eq 0 ]] && continue
    case "$section" in
      added) title=Added ;;
      fixed) title=Fixed ;;
      changed) title=Changed ;;
      removed) title=Removed ;;
    esac
    echo "### $title"
    printf '%s\n' "${entries[@]}"
    echo
  done
} > "$output"

echo "Generated $output from ${last_tag:-repository root} to HEAD."
