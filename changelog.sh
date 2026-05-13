#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
today="$(date +%Y-%m-%d)"

if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  range="HEAD"
  range_label="from repository history"
fi

mapfile -t commits < <(git log "$range" --no-merges --pretty=format:'%s|%h' 2>/dev/null || true)

declare -a added fixed changed removed

categorize_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|add:*|add\ *|added\ *|create:*|create\ *|initial\ *)
      printf 'Added'
      ;;
    fix:*|fix\(*|fixed\ *|bug:*|bugfix:*|hotfix:*|patch:*)
      printf 'Fixed'
      ;;
    remove:*|remove\ *|removed\ *|delete:*|delete\ *|drop:*|drop\ *|deprecate:*)
      printf 'Removed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

append_item() {
  local category="$1"
  local line="$2"
  case "$category" in
    Added) added+=("$line") ;;
    Fixed) fixed+=("$line") ;;
    Removed) removed+=("$line") ;;
    *) changed+=("$line") ;;
  esac
}

for commit in "${commits[@]}"; do
  subject="${commit%|*}"
  sha="${commit##*|}"
  append_item "$(categorize_commit "$subject")" "- ${subject} (${sha})"
done

write_section() {
  local title="$1"
  shift
  local items=("$@")
  {
    echo "## ${title}"
    echo
    if [[ "${#items[@]}" -eq 0 ]]; then
      echo "- No changes."
    else
      printf '%s\n' "${items[@]}"
    fi
    echo
  } >>"$OUTPUT_FILE"
}

{
  echo "# Changelog"
  echo
  echo "Generated for ${repo_name} on ${today} (${range_label})."
  echo
} >"$OUTPUT_FILE"

if [[ "${#commits[@]}" -eq 0 ]]; then
  {
    echo "No commits found for ${range_label}."
    echo
  } >>"$OUTPUT_FILE"
else
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
fi

echo "Wrote ${OUTPUT_FILE}"
