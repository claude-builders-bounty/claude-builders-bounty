#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [output-file]

Generates a structured changelog from commits since the latest git tag.
If the repository has no tags, all commits are included.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

output_file="${1:-CHANGELOG.md}"
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

latest_tag=""
range_label="initial history"
range_args=()

if latest_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  range_label="since ${latest_tag}"
  range_args=("${latest_tag}..HEAD")
fi

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

categorize_subject() {
  local subject="$1"
  local normalized
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feature:*|add:*|added:*|*' add '*|*' adds '*|*' added '*)
      printf 'added'
      ;;
    fix:*|fixed:*|bug:*|bugfix:*|patch:*|*' fix '*|*' fixes '*|*' fixed '*)
      printf 'fixed'
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|*' remove '*|*' removes '*|*' removed '*|*' delete '*|*' deletes '*)
      printf 'removed'
      ;;
    *)
      printf 'changed'
      ;;
  esac
}

while IFS=$'\x1f' read -r short_hash subject || [[ -n "${short_hash:-}${subject:-}" ]]; do
  [[ -z "${short_hash}${subject}" ]] && continue
  entry="- ${subject} (${short_hash})"

  case "$(categorize_subject "$subject")" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    removed) removed+=("$entry") ;;
    *) changed+=("$entry") ;;
  esac
done < <(git log "${range_args[@]}" --no-merges --pretty=format:'%h%x1f%s')

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  if ((${section_count:-0} > 0)); then
    printf '\n'
  fi

  printf '## %s\n\n' "$title"
  if ((${#entries[@]} == 0)); then
    printf -- '- No changes.\n'
    section_count=$((section_count + 1))
    return
  fi

  printf '%s\n' "${entries[@]}"
  section_count=$((section_count + 1))
}

{
  printf '# Changelog\n\n'
  printf '_Generated from git history %s on %s._\n\n' "$range_label" "$(date -u +%Y-%m-%d)"

  if ((${#added[@]} + ${#fixed[@]} + ${#changed[@]} + ${#removed[@]} == 0)); then
    printf 'No commits found %s.\n' "$range_label"
  else
    section_count=0
    write_section "Added" "${added[@]}"
    write_section "Fixed" "${fixed[@]}"
    write_section "Changed" "${changed[@]}"
    write_section "Removed" "${removed[@]}"
  fi
} > "$output_file"

echo "Wrote ${output_file}"
