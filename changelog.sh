#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must run inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$latest_tag" ]; then
  revision_range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  revision_range="HEAD"
  since_label="for full history"
fi

commit_lines="$(git log "$revision_range" --no-merges --pretty=format:'%s|%h' 2>/dev/null || true)"
today="$(date +%Y-%m-%d)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

add_item() {
  local bucket="$1"
  local text="$2"
  case "$bucket" in
    added) added+=("$text") ;;
    fixed) fixed+=("$text") ;;
    changed) changed+=("$text") ;;
    removed) removed+=("$text") ;;
  esac
}

while IFS='|' read -r subject hash; do
  [ -n "${subject:-}" ] || continue
  entry="${subject} (${hash})"
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|add:*|added:*|*' add '*|*' adds '*)
      add_item added "$entry"
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|*' fix '*|*' fixes '*)
      add_item fixed "$entry"
      ;;
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|deprecated:*|*' remove '*|*' delete '*)
      add_item removed "$entry"
      ;;
    *)
      add_item changed "$entry"
      ;;
  esac
done <<< "$commit_lines"

write_section() {
  local title="$1"
  shift
  local items=("$@")
  {
    echo "### ${title}"
    if [ "${#items[@]}" -eq 0 ]; then
      echo "- No changes."
    else
      for item in "${items[@]}"; do
        echo "- ${item}"
      done
    fi
    echo
  } >> "$output_file"
}

{
  echo "# Changelog"
  echo
  echo "## ${today} - ${since_label}"
  echo
} > "$output_file"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

echo "Wrote ${output_file}"
