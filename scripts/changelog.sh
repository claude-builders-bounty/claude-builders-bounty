#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required to generate a changelog" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Run this script inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  range="HEAD"
  range_label="from repository history"
fi

commits=()
while IFS= read -r commit || [[ -n "$commit" ]]; do
  commits+=("$commit")
done < <(git log "$range" --no-merges --pretty=format:'%H%x09%s')

if [[ "${#commits[@]}" -eq 0 ]]; then
  {
    echo "# Changelog"
    echo
    echo "Generated on $(date +%F) (${range_label})."
    echo
    echo "No commits found for this range."
  } > "$OUTPUT_FILE"
  echo "Wrote ${OUTPUT_FILE}"
  exit 0
fi

added_entries=""
fixed_entries=""
changed_entries=""
removed_entries=""

categorize_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    revert*|remove*|removed*|delete*|deleted*|drop*|dropped*|deprecat*)
      echo "removed"
      ;;
    fix*|bug*|patch*|resolve*|resolved*|repair*)
      echo "fixed"
      ;;
    feat*|add*|added*|create*|created*|implement*|implemented*|introduce*|introduced*|support*)
      echo "added"
      ;;
    refactor*|perf*|improve*|improved*|update*|updated*|change*|changed*|chore*|docs*|test*|ci*|build*)
      echo "changed"
      ;;
    *)
      if [[ "$lower" == *" remove "* || "$lower" == *" delete "* || "$lower" == *" drop "* ]]; then
        echo "removed"
      elif [[ "$lower" == *" fix "* || "$lower" == *" bug "* || "$lower" == *" error "* ]]; then
        echo "fixed"
      elif [[ "$lower" == *" add "* || "$lower" == *" support "* || "$lower" == *" implement "* ]]; then
        echo "added"
      else
        echo "changed"
      fi
      ;;
  esac
}

format_entry() {
  local hash="$1"
  local subject="$2"
  printf -- "- %s (%s)\n" "$subject" "${hash:0:7}"
}

for commit in "${commits[@]}"; do
  hash="${commit%%$'\t'*}"
  subject="${commit#*$'\t'}"
  entry="$(format_entry "$hash" "$subject")"

  case "$(categorize_commit "$subject")" in
    added) added_entries+="$entry" ;;
    fixed) fixed_entries+="$entry" ;;
    removed) removed_entries+="$entry" ;;
    *) changed_entries+="$entry" ;;
  esac
done

write_section() {
  local title="$1"
  local entries="$2"

  if [[ -z "$entries" ]]; then
    return
  fi

  echo "## ${title}"
  echo
  printf '%s' "$entries"
  echo
}

{
  echo "# Changelog"
  echo
  echo "Generated on $(date +%F) (${range_label})."
  echo
  write_section "Added" "$added_entries"
  write_section "Fixed" "$fixed_entries"
  write_section "Changed" "$changed_entries"
  write_section "Removed" "$removed_entries"
} > "$OUTPUT_FILE"

echo "Wrote ${OUTPUT_FILE}"
