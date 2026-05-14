#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
TODAY="$(date +%Y-%m-%d)"

die() {
  printf 'generate-changelog: %s\n' "$1" >&2
  exit 1
}

require_git_repo() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
    die "run this from inside a git repository"
}

repo_root() {
  git rev-parse --show-toplevel
}

maybe_fetch_tags() {
  if [[ "${CHANGELOG_FETCH_TAGS:-1}" == "0" ]]; then
    return
  fi

  if git remote get-url origin >/dev/null 2>&1; then
    git fetch --tags --quiet origin >/dev/null 2>&1 || true
  fi
}

latest_tag() {
  git describe --tags --abbrev=0 2>/dev/null || true
}

commit_range() {
  local tag="$1"
  if [[ -n "$tag" ]]; then
    printf '%s..HEAD\n' "$tag"
  else
    printf 'HEAD\n'
  fi
}

human_range() {
  local tag="$1"
  if [[ -n "$tag" ]]; then
    printf 'Changes since `%s`.' "$tag"
  else
    printf 'Changes from the full repository history because no git tag was found.'
  fi
}

clean_subject() {
  local subject="$1"
  local conventional='^[A-Za-z]+(\([^)]+\))?!?:[[:space:]]*(.+)$'

  if [[ "$subject" =~ $conventional ]]; then
    printf '%s' "${BASH_REMATCH[2]}"
  else
    printf '%s' "$subject"
  fi
}

category_for() {
  local subject
  subject="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  if [[ "$subject" =~ (^|[^a-z])(remove|removed|removes|delete|deleted|deletes|drop|dropped|deprecate|deprecated)([^a-z]|$) ]]; then
    printf 'Removed'
  elif [[ "$subject" =~ (^|[^a-z])(fix|fixed|fixes|bugfix|bug|resolve|resolved|patch)([^a-z]|$) || "$subject" =~ ^(fix|hotfix)(\(|:|!) ]]; then
    printf 'Fixed'
  elif [[ "$subject" =~ (^|[^a-z])(add|added|adds|create|created|creates|new|introduce|introduced|implement|implemented)([^a-z]|$) || "$subject" =~ ^feat(\(|:|!) ]]; then
    printf 'Added'
  else
    printf 'Changed'
  fi
}

append_unique() {
  local file="$1"
  local item="$2"

  grep -Fxq -- "$item" "$file" 2>/dev/null || printf '%s\n' "$item" >>"$file"
}

write_category() {
  local title="$1"
  local file="$2"

  printf '### %s\n' "$title"
  if [[ -s "$file" ]]; then
    cat "$file"
  else
    printf '%s\n' '- No entries.'
  fi
  printf '\n'
}

prepend_or_create_changelog() {
  local output="$1"
  local section="$2"
  local tmp_output
  tmp_output="$(mktemp)"

  if [[ -f "$output" ]]; then
    {
      printf '# Changelog\n\n'
      cat "$section"
      awk 'NR == 1 && /^# Changelog/ { next } { print }' "$output"
    } >"$tmp_output"
  else
    {
      printf '# Changelog\n\n'
      cat "$section"
    } >"$tmp_output"
  fi

  mv "$tmp_output" "$output"
}

main() {
  require_git_repo
  cd "$(repo_root)"
  maybe_fetch_tags

  local tag range commits_count
  tag="$(latest_tag)"
  range="$(commit_range "$tag")"
  commits_count="$(git rev-list --count "$range" 2>/dev/null || printf '0')"

  local tmp_dir added fixed changed removed section
  CHANGELOG_TMP_DIR="$(mktemp -d)"
  tmp_dir="$CHANGELOG_TMP_DIR"
  trap 'rm -rf "${CHANGELOG_TMP_DIR:-}"' EXIT

  added="$tmp_dir/added"
  fixed="$tmp_dir/fixed"
  changed="$tmp_dir/changed"
  removed="$tmp_dir/removed"
  section="$tmp_dir/section"
  touch "$added" "$fixed" "$changed" "$removed"

  while IFS=$'\t' read -r short_hash subject; do
    [[ -n "${subject:-}" ]] || continue

    local cleaned category item target
    cleaned="$(clean_subject "$subject")"
    category="$(category_for "$subject")"
    item="- ${cleaned} (${short_hash})"

    case "$category" in
      Added) target="$added" ;;
      Fixed) target="$fixed" ;;
      Removed) target="$removed" ;;
      *) target="$changed" ;;
    esac

    append_unique "$target" "$item"
  done < <(git log --reverse --format='%h%x09%s' "$range")

  {
    printf '## Unreleased - %s\n\n' "$TODAY"
    printf '%s Commit count: %s.\n\n' "$(human_range "$tag")" "$commits_count"
    write_category "Added" "$added"
    write_category "Fixed" "$fixed"
    write_category "Changed" "$changed"
    write_category "Removed" "$removed"
  } >"$section"

  prepend_or_create_changelog "$OUTPUT_FILE" "$section"
  printf 'Wrote %s with %s commit(s) from %s.\n' "$OUTPUT_FILE" "$commits_count" "$range"
}

main "$@"
