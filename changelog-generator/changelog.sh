#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$latest_tag" ]]; then
  range="$latest_tag..HEAD"
  range_label="since $latest_tag"
else
  range="HEAD"
  range_label="for entire history"
fi

commits="$(git log "$range" --no-merges --pretty=format:'%h%x09%s' || true)"
today="$(date +%Y-%m-%d)"

declare -a added fixed changed removed

categorize_commit() {
  local sha="$1"
  local subject="$2"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  local line="- ${subject} (${sha})"

  case "$lower" in
    feat:*|feature:*|add:*|added:*|*' add '*|*' adds '*)
      added+=("$line")
      ;;
    fix:*|bugfix:*|bug:*|*' fix '*|*' fixes '*|*' fixed '*)
      fixed+=("$line")
      ;;
    remove:*|removed:*|delete:*|deleted:*|*' remove '*|*' removes '*|*' delete '*)
      removed+=("$line")
      ;;
    refactor:*|change:*|changed:*|perf:*|docs:*|style:*|chore:*|build:*|ci:*|test:*)
      changed+=("$line")
      ;;
    *)
      changed+=("$line")
      ;;
  esac
}

while IFS=$'\t' read -r sha subject; do
  [[ -z "${sha:-}" ]] && continue
  categorize_commit "$sha" "$subject"
done <<< "$commits"

write_section() {
  local title="$1"
  local array_name="$2"
  local count
  eval "count=\${#$array_name[@]}"
  if [[ "$count" -eq 0 ]]; then
    return
  fi
  {
    echo
    echo "### $title"
    eval "printf '%s\n' \"\${$array_name[@]}\""
  } >> "$output_file"
}

{
  echo "# Changelog"
  echo
  echo "All notable changes are grouped from git commit history."
  echo
  echo "## [Unreleased] - $today"
  echo
  echo "_Generated $range_label._"
} > "$output_file"

write_section "Added" added
write_section "Fixed" fixed
write_section "Changed" changed
write_section "Removed" removed

if [[ -z "$commits" ]]; then
  {
    echo
    echo "No commits found $range_label."
  } >> "$output_file"
fi

echo "Wrote $output_file $range_label"
