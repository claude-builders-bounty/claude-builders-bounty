#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
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

commit_count="$(git rev-list --count "$range" 2>/dev/null || echo 0)"
if [[ "$commit_count" -eq 0 ]]; then
  echo "Error: no commits found for ${range_label}." >&2
  exit 1
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash:-}" ]] && continue

  short_hash="${hash:0:7}"
  entry="- ${subject} (${short_hash})"
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feature:*|add:*|added:*|*' add '*|*' adds '*|*' introduce '*|*' introduces '*)
      added+=("$entry")
      ;;
    fix:*|bugfix:*|hotfix:*|*' fix '*|*' fixes '*|*' fixed '*|*' bug '*)
      fixed+=("$entry")
      ;;
    remove:*|removed:*|delete:*|deleted:*|*' remove '*|*' removes '*|*' delete '*|*' deletes '*)
      removed+=("$entry")
      ;;
    *)
      changed+=("$entry")
      ;;
  esac
done < <(git log --reverse --format='%H%x09%s' "$range")

write_section() {
  local title="$1"
  shift

  {
    echo "## ${title}"
    echo
    if (($# == 0)); then
      echo "- No changes."
    else
      printf '%s\n' "$@"
    fi
    echo
  } >>"$output_file"
}

{
  echo "# Changelog"
  echo
  echo "Generated on $(date -u +%Y-%m-%d) ${range_label}."
  echo
} >"$output_file"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

echo "Wrote ${output_file}"
