#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: run this script from inside a git repository" >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  range_label="since ${last_tag}"
else
  range="HEAD"
  range_label="from full git history"
fi

commits="$(git log --reverse --pretty=format:'%s' "$range")"

if [[ -z "$commits" ]]; then
  {
    echo "# Changelog"
    echo
    echo "No commits found ${range_label}."
  } > "$OUTPUT_FILE"
  echo "Wrote $OUTPUT_FILE"
  exit 0
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

clean_subject() {
  local subject="$1"
  subject="${subject#feat: }"
  subject="${subject#feature: }"
  subject="${subject#fix: }"
  subject="${subject#bugfix: }"
  subject="${subject#docs: }"
  subject="${subject#doc: }"
  subject="${subject#refactor: }"
  subject="${subject#perf: }"
  subject="${subject#chore: }"
  subject="${subject#remove: }"
  subject="${subject#removed: }"
  subject="${subject#delete: }"
  subject="${subject#deleted: }"
  printf '%s' "$subject"
}

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue

  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  entry="$(clean_subject "$subject")"

  case "$normalized" in
    feat:*|feature:*|add:*|added:*|*' add '*|*' added '*)
      added+=("$entry")
      ;;
    fix:*|bugfix:*|hotfix:*|*fix*|*bug*)
      fixed+=("$entry")
      ;;
    remove:*|removed:*|delete:*|deleted:*|*remove*|*delete*)
      removed+=("$entry")
      ;;
    *)
      changed+=("$entry")
      ;;
  esac
done <<< "$commits"

write_section() {
  local title="$1"
  shift
  local items=("$@")

  echo "## $title"
  echo

  if [[ "${#items[@]}" -eq 0 ]]; then
    echo "- No changes."
  else
    local item
    for item in "${items[@]}"; do
      echo "- $item"
    done
  fi

  echo
}

{
  echo "# Changelog"
  echo
  echo "Generated $(date -u '+%Y-%m-%d') ${range_label}."
  echo
  write_section "Added" ${added[@]+"${added[@]}"}
  write_section "Fixed" ${fixed[@]+"${fixed[@]}"}
  write_section "Changed" ${changed[@]+"${changed[@]}"}
  write_section "Removed" ${removed[@]+"${removed[@]}"}
} > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE"
