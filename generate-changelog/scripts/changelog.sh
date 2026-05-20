#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

today="$(date +%Y-%m-%d)"
last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$last_tag" ]]; then
  range="$last_tag..HEAD"
  source_label="commits since \`$last_tag\`"
else
  range="HEAD"
  source_label="all commits"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added="$tmp_dir/added"
fixed="$tmp_dir/fixed"
changed="$tmp_dir/changed"
removed="$tmp_dir/removed"
: >"$added"
: >"$fixed"
: >"$changed"
: >"$removed"

clean_subject() {
  local subject="$1"
  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  printf '%s' "$subject" | sed -E 's/[[:space:]]+/ /g; s/^[[:space:]]+//; s/[[:space:]]+$//'
}

category_for() {
  local subject_lc="$1"
  if [[ "$subject_lc" =~ ^feat(\(.+\))?!?: ]] || [[ "$subject_lc" =~ (^|[[:space:]])(add|create|implement|introduce)(s|ed|ing)?([[:space:]]|$) ]]; then
    echo "added"
  elif [[ "$subject_lc" =~ ^fix(\(.+\))?!?: ]] || [[ "$subject_lc" =~ (^|[[:space:]])(fix|bug|repair|resolve)(s|ed|ing)?([[:space:]]|$) ]]; then
    echo "fixed"
  elif [[ "$subject_lc" =~ ^(remove|delete)(\(.+\))?!?: ]] || [[ "$subject_lc" =~ (^|[[:space:]])(remove|delete|drop|deprecate)(s|d|ing)?([[:space:]]|$) ]]; then
    echo "removed"
  else
    echo "changed"
  fi
}

commit_count=0
while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  commit_count=$((commit_count + 1))
  cleaned="$(clean_subject "$subject")"
  [[ -z "$cleaned" ]] && cleaned="$subject"
  category="$(category_for "$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')")"
  printf -- "- %s\n" "$cleaned" >>"$tmp_dir/$category"
done < <(git log --no-merges --format=%s "$range")

write_section() {
  local title="$1"
  local file="$2"
  printf "### %s\n\n" "$title"
  if [[ -s "$file" ]]; then
    sort -u "$file"
  else
    printf -- "- No changes.\n"
  fi
  printf "\n"
}

new_section="$tmp_dir/new-section.md"
{
  printf "## Unreleased - %s\n\n" "$today"
  printf "Generated from %s (%s commit%s).\n\n" "$source_label" "$commit_count" "$([[ "$commit_count" == "1" ]] && printf "" || printf "s")"
  write_section "Added" "$added"
  write_section "Fixed" "$fixed"
  write_section "Changed" "$changed"
  write_section "Removed" "$removed"
} >"$new_section"

if [[ -f "$OUTPUT" ]]; then
  body_file="$tmp_dir/body.md"
  sed '1{/^# Changelog$/d;}' "$OUTPUT" >"$body_file"
  {
    printf "# Changelog\n\n"
    cat "$new_section"
    cat "$body_file"
  } >"$OUTPUT"
else
  {
    printf "# Changelog\n\n"
    cat "$new_section"
  } >"$OUTPUT"
fi

echo "Wrote $OUTPUT from $commit_count commit(s) ($source_label)."
