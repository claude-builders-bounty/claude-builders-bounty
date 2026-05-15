#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  git fetch --tags --quiet origin >/dev/null 2>&1 || true
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
range="HEAD"
range_label="all commits"

if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  range_label="commits since ${latest_tag}"
fi

commit_lines="$(git log "$range" --no-merges --pretty=format:'%s%x09%h' 2>/dev/null || true)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()

append_entry() {
  local bucket="$1"
  local subject="$2"
  local short_sha="$3"
  local entry="- ${subject} (${short_sha})"

  case "$bucket" in
    added) added+=("$entry") ;;
    fixed) fixed+=("$entry") ;;
    changed) changed+=("$entry") ;;
    removed) removed+=("$entry") ;;
  esac
}

categorize_subject() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|feature:*|add:*|added:*|create:*|implement:*|introduce:*) echo "added" ;;
    fix:*|fix\(*|bugfix:*|hotfix:*|repair:*|resolve:*|patch:*) echo "fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*|deprecated:*) echo "removed" ;;
    refactor:*|refactor\(*|change:*|changed:*|update:*|updated:*|docs:*|docs\(*|style:*|perf:*|test:*|chore:*) echo "changed" ;;
    *)
      if [[ "$lower" =~ (^|[[:space:]])(fix|fixed|bug|bugfix|resolve|resolved)([[:space:]]|:|$) ]]; then
        echo "fixed"
      elif [[ "$lower" =~ (^|[[:space:]])(remove|removed|delete|deleted|drop|dropped)([[:space:]]|:|$) ]]; then
        echo "removed"
      elif [[ "$lower" =~ (^|[[:space:]])(add|added|create|created|implement|implemented|introduce|introduced)([[:space:]]|:|$) ]]; then
        echo "added"
      else
        echo "changed"
      fi
      ;;
  esac
}

if [[ -n "$commit_lines" ]]; then
  while IFS=$'\t' read -r subject short_sha; do
    [[ -z "$subject" ]] && continue
    append_entry "$(categorize_subject "$subject")" "$subject" "$short_sha"
  done <<< "$commit_lines"
fi

write_section() {
  local title="$1"
  shift

  printf '### %s\n\n' "$title"
  if (($# == 0)); then
    printf -- '- No changes.\n\n'
    return
  fi

  printf '%s\n' "$@"
  printf '\n'
}

write_bucket() {
  local title="$1"
  local bucket="$2"

  case "$bucket" in
    added)
      if ((${#added[@]} == 0)); then write_section "$title"; else write_section "$title" "${added[@]}"; fi
      ;;
    fixed)
      if ((${#fixed[@]} == 0)); then write_section "$title"; else write_section "$title" "${fixed[@]}"; fi
      ;;
    changed)
      if ((${#changed[@]} == 0)); then write_section "$title"; else write_section "$title" "${changed[@]}"; fi
      ;;
    removed)
      if ((${#removed[@]} == 0)); then write_section "$title"; else write_section "$title" "${removed[@]}"; fi
      ;;
  esac
}

{
  printf '# Changelog\n\n'
  printf 'Generated from %s on %s.\n\n' "$range_label" "$(date -u '+%Y-%m-%d')"
  write_bucket "Added" added
  write_bucket "Fixed" fixed
  write_bucket "Changed" changed
  write_bucket "Removed" removed
} > "$output_file"

echo "Wrote ${output_file} from ${range_label}."
