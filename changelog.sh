#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  range_label="since ${last_tag}"
else
  range="HEAD"
  range_label="for all commits; no git tag was found"
fi

commit_lines="$(git log "$range" --no-merges --date=short --pretty=format:'%H%x1f%s%x1f%an%x1f%ad' || true)"
generated_at="$(date -u +"%Y-%m-%d")"

added=()
fixed=()
changed=()
removed=()

clean_subject() {
  local subject="$1"
  subject="${subject#feat: }"
  subject="${subject#fix: }"
  subject="${subject#chore: }"
  subject="${subject#docs: }"
  subject="${subject#refactor: }"
  subject="${subject#perf: }"
  subject="${subject#test: }"
  subject="${subject#remove: }"
  subject="${subject#removed: }"
  subject="${subject#change: }"
  subject="${subject#changed: }"
  printf '%s' "$subject"
}

categorize() {
  local subject_lower="$1"
  case "$subject_lower" in
    feat:*|feature:*|add:*|added:*|adding\ *|add\ *|adds\ *|added\ *|create:*|create\ *|created\ *|implement:*|implement\ *|implemented\ *|*" add "*|*" adds "*|*" added "*|*" implement "*)
      printf 'Added'
      ;;
    fix:*|fixed:*|fix\ *|fixes\ *|fixed\ *|bug:*|bug\ *|patch:*|patch\ *|repair:*|repair\ *|*" fix "*|*" fixes "*|*" fixed "*|*" bug "*)
      printf 'Fixed'
      ;;
    remove:*|removed:*|remove\ *|removed\ *|delete:*|deleted:*|delete\ *|deleted\ *|drop:*|dropped:*|drop\ *|dropped\ *|deprecate:*|deprecated:*|deprecate\ *|deprecated\ *|*" remove "*|*" delete "*|*" drop "*)
      printf 'Removed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

append_item() {
  local category="$1"
  local subject="$2"
  local sha="$3"
  local author="$4"
  local date="$5"
  local short_sha="${sha:0:7}"
  local item="- $(clean_subject "$subject") (${short_sha}, ${date}, ${author})"
  case "$category" in
    Added) added+=("$item") ;;
    Fixed) fixed+=("$item") ;;
    Removed) removed+=("$item") ;;
    *) changed+=("$item") ;;
  esac
}

if [[ -n "$commit_lines" ]]; then
  while IFS=$'\x1f' read -r sha subject author date; do
    [[ -z "${sha:-}" ]] && continue
    subject_lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
    append_item "$(categorize "$subject_lower")" "$subject" "$sha" "$author" "$date"
  done <<< "$commit_lines"
fi

write_section() {
  local title="$1"
  shift
  local items=("$@")
  {
    echo "### ${title}"
    echo
    if [[ "${#items[@]}" -eq 0 ]]; then
      echo "- No ${title,,} changes detected."
    else
      printf '%s\n' "${items[@]}"
    fi
    echo
  } >> "$OUTPUT_FILE"
}

{
  echo "# Changelog"
  echo
  echo "Generated for \`${repo_name}\` on ${generated_at}, ${range_label}."
  echo
  if [[ -n "$last_tag" ]]; then
    echo "Commit range: \`${last_tag}..HEAD\`"
  else
    echo "Commit range: \`HEAD\`"
  fi
  echo
} > "$OUTPUT_FILE"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

echo "Wrote ${OUTPUT_FILE}"
