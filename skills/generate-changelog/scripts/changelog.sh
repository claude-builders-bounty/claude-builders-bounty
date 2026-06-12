#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh: must be run inside a git repository" >&2
  exit 1
fi

latest_tag=""
if latest_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range="${latest_tag}..HEAD"
else
  range="HEAD"
fi

commit_lines="$(git log "${range}" --no-merges --pretty=format:'%s%x09%h')"
today="$(date +%Y-%m-%d)"

added=()
fixed=()
changed=()
removed=()

append_item() {
  local category="$1"
  local subject="$2"
  local hash="$3"
  local item="- ${subject} (${hash})"

  case "$category" in
    added) added+=("$item") ;;
    fixed) fixed+=("$item") ;;
    changed) changed+=("$item") ;;
    removed) removed+=("$item") ;;
  esac
}

categorize() {
  local subject_lower="$1"
  case "$subject_lower" in
    feat:*|feat\(*|add:*|add\(*|new:*|new\(*) echo "added" ;;
    fix:*|fix\(*|bug:*|bug\(*|patch:*|patch\(*) echo "fixed" ;;
    remove:*|remove\(*|delete:*|delete\(*|drop:*|drop\(*|deprecate:*|deprecate\(*) echo "removed" ;;
    change:*|change\(*|refactor:*|refactor\(*|perf:*|perf\(*|docs:*|docs\(*|chore:*|chore\(*|build:*|build\(*|ci:*|ci\(*|test:*|test\(*|style:*|style\(*) echo "changed" ;;
    *) echo "changed" ;;
  esac
}

if [[ -n "$commit_lines" ]]; then
  while IFS=$'\t' read -r subject hash; do
    [[ -z "${subject}" ]] && continue
    lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
    append_item "$(categorize "$lower")" "$subject" "$hash"
  done <<< "$commit_lines"
fi

write_section() {
  local title="$1"
  local trailing_blank="$2"
  shift
  shift
  local items=("$@")
  {
    echo "### ${title}"
    echo
    if ((${#items[@]} == 0)); then
      echo "- No changes."
    else
      printf '%s\n' "${items[@]}"
    fi
    if [[ "$trailing_blank" == "yes" ]]; then
      echo
    fi
  } >> "$output_file"
}

{
  echo "# Changelog"
  echo
  echo "All notable changes to this project will be documented in this file."
  echo
  if [[ -n "$latest_tag" ]]; then
    echo "## Unreleased - ${today}"
    echo
    echo "_Changes since ${latest_tag}._"
  else
    echo "## Initial history - ${today}"
    echo
    echo "_No git tag found; using full commit history._"
  fi
  echo
} > "$output_file"

write_section "Added" "yes" "${added[@]}"
write_section "Fixed" "yes" "${fixed[@]}"
write_section "Changed" "yes" "${changed[@]}"
write_section "Removed" "no" "${removed[@]}"

echo "Wrote ${output_file}"
