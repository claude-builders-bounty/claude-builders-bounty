#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required to generate the changelog." >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: run this script from inside a git repository." >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$last_tag" ]; then
  commit_range="${last_tag}..HEAD"
  since_label="since ${last_tag}"
else
  commit_range="HEAD"
  since_label="from initial commit"
fi

mapfile -t commits < <(git log "$commit_range" --pretty=format:'%s%x09%h')

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_commit() {
  local subject="$1"
  local hash="$2"
  local entry="- ${subject} (${hash})"
  local normalized
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feature:*|add:*|added:*|*' add '*|*' added '*)
      added+=("$entry")
      ;;
    fix:*|fixed:*|bugfix:*|hotfix:*|*' fix '*|*' fixed '*|*bug*)
      fixed+=("$entry")
      ;;
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|deprecated:*|*' remove '*|*' removed '*)
      removed+=("$entry")
      ;;
    refactor:*|change:*|changed:*|chore:*|docs:*|test:*|perf:*|style:*|build:*|ci:*)
      changed+=("$entry")
      ;;
    *)
      changed+=("$entry")
      ;;
  esac
}

for commit in "${commits[@]}"; do
  subject="${commit%$'\t'*}"
  hash="${commit##*$'\t'}"
  [ -n "$subject" ] && append_commit "$subject" "$hash"
done

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  {
    echo "## ${title}"
    echo
    if [ "${#entries[@]}" -eq 0 ]; then
      echo "- No changes."
    else
      printf '%s\n' "${entries[@]}"
    fi
    echo
  } >> "$output_file"
}

{
  echo "# Changelog"
  echo
  echo "Generated on $(date -u +%Y-%m-%d) for commits ${since_label}."
  echo
} > "$output_file"

write_section "Added" "${added[@]}"
write_section "Fixed" "${fixed[@]}"
write_section "Changed" "${changed[@]}"
write_section "Removed" "${removed[@]}"

echo "Wrote ${output_file}"
