#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag=""
if latest_tag=$(git describe --tags --abbrev=0 2>/dev/null); then
  range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  range="HEAD"
  range_label="from all commits"
fi

commit_lines=$(git log "$range" --no-merges --pretty=format:'%h%x09%s' || true)

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_item() {
  local category="$1"
  local item="$2"

  case "$category" in
    added) added+=("$item") ;;
    fixed) fixed+=("$item") ;;
    removed) removed+=("$item") ;;
    *) changed+=("$item") ;;
  esac
}

categorize_subject() {
  local subject_lower="$1"

  case "$subject_lower" in
    feat:*|feat\(*|add:*|add\ *|create:*|create\ *|implement:*|implement\ *)
      echo "added"
      ;;
    fix:*|fix\(*|bug:*|bug\ *|patch:*|patch\ *|repair:*|repair\ *|resolve:*|resolve\ *)
      echo "fixed"
      ;;
    remove:*|remove\ *|delete:*|delete\ *|drop:*|drop\ *|deprecate:*|deprecate\ *)
      echo "removed"
      ;;
    *)
      echo "changed"
      ;;
  esac
}

if [ -n "$commit_lines" ]; then
  while IFS=$'\t' read -r sha subject; do
    [ -n "${sha:-}" ] || continue
    subject="${subject:-No subject}"
    subject_lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')
    category=$(categorize_subject "$subject_lower")
    append_item "$category" "${subject} (${sha})"
  done <<< "$commit_lines"
fi

write_section() {
  local title="$1"
  shift
  local items=("$@")

  {
    echo "### ${title}"
    echo
    if [ "${#items[@]}" -eq 0 ]; then
      echo "- No changes."
    else
      for item in "${items[@]}"; do
        echo "- ${item}"
      done
    fi
    echo
  } >> "$OUTPUT_FILE"
}

{
  echo "# Changelog"
  echo
  echo "Generated on $(date -u '+%Y-%m-%d') ${range_label}."
  echo
  echo "## Unreleased"
  echo
} > "$OUTPUT_FILE"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

echo "Wrote ${OUTPUT_FILE}"
