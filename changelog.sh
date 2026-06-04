#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository." >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
today="$(date +%Y-%m-%d)"

if [[ -n "$last_tag" ]]; then
  range="${last_tag}..HEAD"
  scope="Changes since \`$last_tag\`."
else
  range="HEAD"
  scope="All commits. No git tags found."
fi

added=()
fixed=()
changed=()
removed=()

clean_subject() {
  local subject="$1"

  subject="${subject#revert: }"
  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"

  if [[ -z "$subject" ]]; then
    subject="Untitled change"
  fi

  printf '%s' "$subject"
}

add_entry() {
  local subject="$1"
  local hash="$2"
  local entry="- $(clean_subject "$subject") (\`$hash\`)"
  local lower

  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*|*' remove '*|*' delete '*|*' drop '*)
      removed+=("$entry")
      ;;
    fix:*|fixed:*|bugfix:*|bug:*|patch:*|resolve:*|resolved:*|repair:*|repaired:*|*' fix '*|*' bug '*)
      fixed+=("$entry")
      ;;
    feat:*|feature:*|add:*|added:*|create:*|created:*|implement:*|implemented:*|introduce:*|introduced:*|initial:*)
      added+=("$entry")
      ;;
    *)
      changed+=("$entry")
      ;;
  esac
}

while IFS=$'\t' read -r subject hash || [[ -n "${subject:-}" ]]; do
  [[ -z "${subject:-}" || -z "${hash:-}" ]] && continue
  add_entry "$subject" "$hash"
done < <(git log "$range" --reverse --pretty=format:'%s%x09%h')

write_section() {
  local title="$1"
  local array_name="$2"
  local -n entries="$array_name"

  {
    printf '### %s\n' "$title"
    if ((${#entries[@]} == 0)); then
      printf -- '- None\n'
    else
      printf '%s\n' "${entries[@]}"
    fi
    printf '\n'
  } >>"$output_file"
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$today"
  printf '%s\n\n' "$scope"
} >"$output_file"

write_section "Added" added
write_section "Fixed" fixed
write_section "Changed" changed
write_section "Removed" removed

echo "Wrote $output_file"
