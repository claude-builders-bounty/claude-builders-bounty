#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: run this script inside a git repository" >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$last_tag" ]]; then
  range="$last_tag..HEAD"
  scope="since $last_tag"
else
  range="HEAD"
  scope="from the first commit"
fi

today="$(date +%Y-%m-%d)"
tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

while IFS=$'\x1f' read -r sha subject || [[ -n "${sha:-}" ]]; do
  [[ -z "${sha:-}" || -z "${subject:-}" ]] && continue
  short_sha="$(git rev-parse --short "$sha")"
  entry="- ${subject} (${short_sha})"
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feature:*|add*|create*|implement*|init*|support*|new*)
      added+=("$entry")
      ;;
    fix:*|bug:*|repair*|resolve*|correct*|patch*)
      fixed+=("$entry")
      ;;
    remove*|delete*|drop*|deprecat*)
      removed+=("$entry")
      ;;
    *)
      changed+=("$entry")
      ;;
  esac
done < <(git log --no-merges --reverse --pretty=format:'%H%x1f%s' "$range")

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title" >> "$tmp_file"
  if [[ "${#entries[@]}" -eq 0 ]]; then
    printf '_No changes._\n\n' >> "$tmp_file"
    return
  fi

  printf '%s\n' "${entries[@]}" >> "$tmp_file"
  printf '\n' >> "$tmp_file"
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$today"
  printf 'Generated from commits %s.\n\n' "$scope"
} > "$tmp_file"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

mv "$tmp_file" "$output_file"
trap - EXIT

echo "Generated $output_file"
