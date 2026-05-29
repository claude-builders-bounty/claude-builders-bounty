#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range="HEAD"
  since_label="from repository history"
fi

commit_log="$(git log "$range" --no-merges --pretty=format:'%s%x1f%h' 2>/dev/null || true)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_entry() {
  local subject="$1"
  local hash="$2"
  local entry="- ${subject} (${hash})"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|add:*|added:*|new:*|*\ add\ *|*\ adds\ *|*\ added\ *)
      added+=("$entry")
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|*\ fix\ *|*\ fixes\ *|*\ fixed\ *)
      fixed+=("$entry")
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|*\ remove\ *|*\ removes\ *|*\ deleted\ *)
      removed+=("$entry")
      ;;
    *)
      changed+=("$entry")
      ;;
  esac
}

if [[ -n "$commit_log" ]]; then
  while IFS=$'\x1f' read -r subject hash; do
    [[ -z "${subject}" ]] && continue
    append_entry "$subject" "$hash"
  done <<< "$commit_log"
fi

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '## %s\n\n' "$title" >> "$OUTPUT_FILE"
  if [[ ${#entries[@]} -eq 0 ]]; then
    printf -- '- No changes.\n\n' >> "$OUTPUT_FILE"
    return
  fi

  printf '%s\n' "${entries[@]}" >> "$OUTPUT_FILE"
  printf '\n' >> "$OUTPUT_FILE"
}

{
  printf '# Changelog\n\n'
  printf 'Generated on %s %s.\n\n' "$(date -u +%Y-%m-%d)" "$since_label"
} > "$OUTPUT_FILE"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

echo "Generated ${OUTPUT_FILE} ${since_label}."
