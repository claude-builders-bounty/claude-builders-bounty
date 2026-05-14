#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

last_tag=""
if last_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${last_tag}..HEAD"
  since_label="since ${last_tag}"
else
  range="HEAD"
  since_label="from repository history"
fi

mapfile -t commits < <(git log --no-merges --date=short --pretty=format:'%h%x09%ad%x09%s' "$range")

declare -a added fixed changed removed

add_item() {
  local bucket="$1" item="$2"
  case "$bucket" in
    added) added+=("$item") ;;
    fixed) fixed+=("$item") ;;
    changed) changed+=("$item") ;;
    removed) removed+=("$item") ;;
  esac
}

categorize() {
  local subject_lc
  subject_lc=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')
  case "$subject_lc" in
    feat:*|feature:*|add:*|added:*|*' add '*|*' adds '*|*' introduce '*|*' introduces '*) echo added ;;
    fix:*|bugfix:*|hotfix:*|*' fix '*|*' fixes '*|*' fixed '*|*' bug '*|*' patch '*) echo fixed ;;
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|*' remove '*|*' removes '*|*' deleted '*|*' drop '*|*' drops '*) echo removed ;;
    refactor:*|perf:*|docs:*|style:*|test:*|chore:*|ci:*|build:*|change:*|changed:*|update:*|updated:*|*' update '*|*' updates '*|*' change '*|*' changes '*) echo changed ;;
    *) echo changed ;;
  esac
}

for row in "${commits[@]}"; do
  IFS=$'\t' read -r hash date subject <<< "$row"
  bucket=$(categorize "$subject")
  add_item "$bucket" "- ${subject} (${hash}, ${date})"
done

{
  echo "# Changelog"
  echo
  echo "Generated on $(date -u +%Y-%m-%d) ${since_label}."
  echo
  for section in Added Fixed Changed Removed; do
    var=$(printf '%s' "$section" | tr '[:upper:]' '[:lower:]')
    echo "## ${section}"
    echo
    eval 'items=("${'"$var"'[@]}")'
    if [ "${#items[@]}" -eq 0 ]; then
      echo "- No entries."
    else
      printf '%s\n' "${items[@]}"
    fi
    echo
  done
} > "$OUT_FILE"

echo "Generated ${OUT_FILE} with ${#commits[@]} commit(s) ${since_label}."
