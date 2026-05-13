#!/usr/bin/env bash
set -euo pipefail

output_file="${CHANGELOG_FILE:-CHANGELOG.md}"
explicit_range="${CHANGELOG_RANGE:-}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

if [[ -n "$explicit_range" ]]; then
  commit_range="$explicit_range"
  range_label="$explicit_range"
elif latest_tag="$(git describe --tags --abbrev=0 2>/dev/null)"; then
  commit_range="${latest_tag}..HEAD"
  range_label="commits since \`${latest_tag}\`"
else
  commit_range="HEAD"
  range_label="the full git history"
fi

if ! git rev-list --count "$commit_range" >/dev/null 2>&1; then
  echo "error: invalid git range: ${commit_range}" >&2
  exit 1
fi

commit_count="$(git rev-list --count "$commit_range")"
today="$(date +%Y-%m-%d)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

clean_subject() {
  local subject="$1"
  local prefix_re='^[A-Za-z]+(\([^)]+\))?:[[:space:]]*(.*)$'

  if [[ "$subject" =~ $prefix_re ]]; then
    subject="${BASH_REMATCH[2]}"
  fi

  printf '%s' "$subject"
}

append_commit() {
  local hash="$1"
  local subject="$2"
  local lower_subject
  local cleaned
  local entry

  lower_subject="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  cleaned="$(clean_subject "$subject")"
  entry="- ${cleaned} (\`${hash}\`)"

  case "$lower_subject" in
    feat:*|feat\(*\):*|feature:*|feature\(*\):*|add:*|add\ *|added:*|added\ *|*' add '*|*' added '*)
      added+=("$entry")
      ;;
    fix:*|fix\(*\):*|bugfix:*|bugfix\(*\):*|hotfix:*|hotfix\(*\):*|*fixes*|*fixed*|*bug*)
      fixed+=("$entry")
      ;;
    remove:*|remove\ *|removed:*|removed\ *|delete:*|delete\ *|deleted:*|deleted\ *|deprecate:*|deprecate\ *|deprecated:*|deprecated\ *|*remove*|*delete*|*deprecat*)
      removed+=("$entry")
      ;;
    *)
      changed+=("$entry")
      ;;
  esac
}

while IFS=$'\t' read -r hash subject; do
  [[ -z "${hash:-}" ]] && continue
  append_commit "$hash" "$subject"
done < <(git log --no-merges --pretty=format:'%h%x09%s' "$commit_range")

write_section() {
  local title="$1"
  shift
  local entries=("$@")

  printf '### %s\n\n' "$title"
  if ((${#entries[@]} == 0)); then
    printf -- '- No notable changes.\n\n'
    return
  fi

  printf '%s\n' "${entries[@]}"
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased - %s\n\n' "$today"

  if ((commit_count == 0)); then
    printf '_No commits found for %s._\n\n' "$range_label"
  else
    printf '_Generated from %s (%s commit%s)._\n\n' \
      "$range_label" \
      "$commit_count" \
      "$([[ "$commit_count" == "1" ]] && printf '' || printf 's')"
  fi

  set +u
  write_section "Added" "${added[@]}"
  write_section "Fixed" "${fixed[@]}"
  write_section "Changed" "${changed[@]}"
  write_section "Removed" "${removed[@]}"
} > "$output_file"

echo "Generated ${output_file} from ${commit_count} commit(s)."
