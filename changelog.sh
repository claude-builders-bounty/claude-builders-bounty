#!/usr/bin/env bash
set -euo pipefail

output_file="CHANGELOG.md"
repo_dir="."
fetch_tags=1

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [--repo PATH] [--output CHANGELOG.md] [--no-fetch]

Generate a structured CHANGELOG.md from commits since the latest git tag.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      repo_dir="${2:-}"
      shift 2
      ;;
    --output|-o)
      output_file="${2:-}"
      shift 2
      ;;
    --no-fetch)
      fetch_tags=0
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$repo_dir" ] || [ -z "$output_file" ]; then
  echo "--repo and --output require non-empty values" >&2
  exit 2
fi

git_in_repo() {
  git -C "$repo_dir" "$@"
}

if ! git_in_repo rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $repo_dir" >&2
  exit 1
fi

if [ "$fetch_tags" -eq 1 ] && git_in_repo remote get-url origin >/dev/null 2>&1; then
  git_in_repo fetch --tags --quiet >/dev/null 2>&1 || true
fi

last_tag=""
if last_tag_candidate="$(git_in_repo describe --tags --abbrev=0 2>/dev/null)"; then
  last_tag="$last_tag_candidate"
  commit_range="${last_tag}..HEAD"
else
  commit_range="HEAD"
fi

if [ -n "$last_tag" ]; then
  if ! git_in_repo rev-list --quiet "$commit_range" >/dev/null 2>&1; then
    echo "Could not read commit range ${commit_range}" >&2
    exit 1
  fi
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added_file="$tmp_dir/added"
fixed_file="$tmp_dir/fixed"
changed_file="$tmp_dir/changed"
removed_file="$tmp_dir/removed"
touch "$added_file" "$fixed_file" "$changed_file" "$removed_file"

categorize() {
  subject_lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$subject_lower" in
    feat:*|feat\(*|feature:*|add:*|added:*|new:*)
      printf '%s' "Added"
      ;;
    fix:*|fix\(*|bug:*|bugfix:*|hotfix:*|repair:*)
      printf '%s' "Fixed"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|deprecate:*|deprecated:*)
      printf '%s' "Removed"
      ;;
    refactor:*|refactor\(*|change:*|changed:*|update:*|updated:*|perf:*|perf\(*|docs:*|docs\(*|style:*|style\(*|chore:*|chore\(*)
      printf '%s' "Changed"
      ;;
    *)
      if printf '%s' "$subject_lower" | grep -Eq '\b(add|adds|added|create|creates|created|implement|implements|implemented|introduce|introduces|introduced)\b'; then
        printf '%s' "Added"
      elif printf '%s' "$subject_lower" | grep -Eq '\b(fix|fixes|fixed|bug|repair|resolve|resolves|resolved)\b'; then
        printf '%s' "Fixed"
      elif printf '%s' "$subject_lower" | grep -Eq '\b(remove|removes|removed|delete|deletes|deleted|drop|drops|dropped|deprecate|deprecated)\b'; then
        printf '%s' "Removed"
      else
        printf '%s' "Changed"
      fi
      ;;
  esac
}

strip_prefix() {
  printf '%s' "$1" |
    sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//' |
    sed -E 's/^[[:space:]]+|[[:space:]]+$//g'
}

append_entry() {
  category="$1"
  entry="$2"
  case "$category" in
    Added) printf '%s\n' "$entry" >> "$added_file" ;;
    Fixed) printf '%s\n' "$entry" >> "$fixed_file" ;;
    Removed) printf '%s\n' "$entry" >> "$removed_file" ;;
    *) printf '%s\n' "$entry" >> "$changed_file" ;;
  esac
}

while IFS='|' read -r short_hash subject || [ -n "${short_hash:-}" ]; do
  [ -n "$short_hash" ] || continue
  clean_subject="$(strip_prefix "$subject")"
  [ -n "$clean_subject" ] || clean_subject="$subject"
  category="$(categorize "$subject")"
  append_entry "$category" "- ${clean_subject} (${short_hash})"
done < <(git_in_repo log "$commit_range" --no-merges --pretty=format:'%h|%s' --reverse)

today="$(date +%Y-%m-%d)"
repo_name="$(basename "$(git_in_repo rev-parse --show-toplevel)")"
if remote_url="$(git_in_repo remote get-url origin 2>/dev/null)"; then
  case "$remote_url" in
    https://github.com/*)
      repo_name="${remote_url#https://github.com/}"
      repo_name="${repo_name%.git}"
      ;;
    git@github.com:*)
      repo_name="${remote_url#git@github.com:}"
      repo_name="${repo_name%.git}"
      ;;
  esac
fi
tag_label="${last_tag:-initial history}"

write_category() {
  title="$1"
  file="$2"
  if [ -s "$file" ]; then
    printf '\n### %s\n\n' "$title"
    cat "$file"
  fi
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes are generated from git history.\n\n'
  printf '## [Unreleased] - %s\n\n' "$today"
  printf '_Source: commits since %s in `%s`._\n' "$tag_label" "$repo_name"

  if [ ! -s "$added_file" ] && [ ! -s "$fixed_file" ] && [ ! -s "$changed_file" ] && [ ! -s "$removed_file" ]; then
    printf '\nNo commits found since %s.\n' "$tag_label"
  else
    write_category "Added" "$added_file"
    write_category "Fixed" "$fixed_file"
    write_category "Changed" "$changed_file"
    write_category "Removed" "$removed_file"
  fi
} > "$output_file"

echo "Wrote $output_file"
