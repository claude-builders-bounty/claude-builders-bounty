#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag=""
if latest_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${latest_tag}..HEAD"
  since_label="${latest_tag}"
else
  range="HEAD"
  since_label="project start"
fi

if ! git rev-list --count "$range" >/dev/null 2>&1; then
  echo "error: unable to read git history for range: ${range}" >&2
  exit 1
fi

commit_count=$(git rev-list --count "$range")
today=$(date +%Y-%m-%d)
repo_url=$(git config --get remote.origin.url || true)

normalize_subject() {
  local subject="$1"
  subject="${subject#feat: }"; subject="${subject#feature: }"; subject="${subject#add: }"
  subject="${subject#fix: }"; subject="${subject#bug: }"; subject="${subject#hotfix: }"
  subject="${subject#remove: }"; subject="${subject#delete: }"; subject="${subject#deprecate: }"
  subject="${subject#chore: }"; subject="${subject#docs: }"; subject="${subject#refactor: }"; subject="${subject#perf: }"
  subject="${subject#test: }"; subject="${subject#ci: }"; subject="${subject#style: }"
  printf '%s' "$subject"
}

categorize() {
  local subject_lc
  subject_lc=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  case "$subject_lc" in
    feat:*|feature:*|add:*|added:*|*" add "*|*"adds "*|*"new "*) echo "Added" ;;
    fix:*|bug:*|bugfix:*|hotfix:*|*" fix"*|*"bug"*|*"error"*) echo "Fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|*"remove"*|*"delete"*) echo "Removed" ;;
    change:*|changed:*|refactor:*|perf:*|improve:*|improved:*|update:*|updated:*|chore:*|docs:*|ci:*|test:*|style:*) echo "Changed" ;;
    *) echo "Changed" ;;
  esac
}

declare -a added fixed changed removed
while IFS=$'\t' read -r hash subject || [ -n "${hash:-}" ]; do
  [ -n "${hash:-}" ] || continue
  category=$(categorize "$subject")
  cleaned=$(normalize_subject "$subject")
  line="- ${cleaned} (${hash})"
  case "$category" in
    Added) added+=("$line") ;;
    Fixed) fixed+=("$line") ;;
    Removed) removed+=("$line") ;;
    *) changed+=("$line") ;;
  esac
done < <(git log --reverse --pretty=format:'%h%x09%s' "$range")

{
  echo "# Changelog"
  echo
  echo "All notable changes generated from git history."
  echo
  echo "## [Unreleased] - ${today}"
  echo
  echo "_Generated from ${since_label} (${commit_count} commit(s))._"
  if [ -n "$repo_url" ]; then
    echo
    echo "Repository: ${repo_url}"
  fi
  echo
  for section in Added Fixed Changed Removed; do
    case "$section" in
      Added) items=("${added[@]:-}") ;;
      Fixed) items=("${fixed[@]:-}") ;;
      Changed) items=("${changed[@]:-}") ;;
      Removed) items=("${removed[@]:-}") ;;
    esac
    if [ ${#items[@]} -gt 0 ] && [ -n "${items[0]}" ]; then
      echo "### ${section}"
      echo
      printf '%s\n' "${items[@]}"
      echo
    fi
  done
} > "$OUTPUT_FILE"

echo "Wrote ${OUTPUT_FILE} (${commit_count} commit(s), ${since_label})."
