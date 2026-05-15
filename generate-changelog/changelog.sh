#!/usr/bin/env bash
set -euo pipefail

output_file="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
since_ref="${CHANGELOG_SINCE:-}"
include_merges="${CHANGELOG_INCLUDE_MERGES:-0}"

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [options]

Generate a Markdown CHANGELOG.md from commits since the latest Git tag.

Options:
  -o, --output PATH      Output file path (default: CHANGELOG.md)
      --since REF        Use a specific Git ref instead of the latest tag
      --include-merges   Include merge commits
  -h, --help             Show this help

Environment:
  CHANGELOG_OUTPUT       Same as --output
  CHANGELOG_SINCE        Same as --since
  CHANGELOG_INCLUDE_MERGES=1
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    -o|--output)
      if [ "$#" -lt 2 ]; then
        echo "error: $1 requires a path" >&2
        exit 2
      fi
      output_file="$2"
      shift 2
      ;;
    --since)
      if [ "$#" -lt 2 ]; then
        echo "error: --since requires a Git ref" >&2
        exit 2
      fi
      since_ref="$2"
      shift 2
      ;;
    --include-merges)
      include_merges="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v git >/dev/null 2>&1; then
  echo "error: git is required to generate a changelog" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  echo "error: run this command inside a Git repository" >&2
  exit 1
fi

cd "$repo_root"

if [ -z "$since_ref" ]; then
  since_ref="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

range=""
range_note="_Full project history; no Git tags were found._"
if [ -n "$since_ref" ]; then
  if ! git rev-parse --verify --quiet "$since_ref^{commit}" >/dev/null; then
    echo "error: since ref '$since_ref' was not found" >&2
    exit 1
  fi
  range="$since_ref..HEAD"
  range_note="_Changes since \`$since_ref\`._"
fi

case "$output_file" in
  /*|[A-Za-z]:/*|[A-Za-z]:\\*)
    output_path="$output_file"
    ;;
  *)
    output_path="$repo_root/$output_file"
    ;;
esac

output_dir="$(dirname "$output_path")"
mkdir -p "$output_dir"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added_file="$tmp_dir/added.md"
fixed_file="$tmp_dir/fixed.md"
changed_file="$tmp_dir/changed.md"
removed_file="$tmp_dir/removed.md"
touch "$added_file" "$fixed_file" "$changed_file" "$removed_file"

merge_arg="--no-merges"
if [ "$include_merges" = "1" ]; then
  merge_arg=""
fi

categorize_commit() {
  subject_lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"

  if [[ "$subject_lower" =~ ^(feat|feature)(\(.+\))?(!)?: ]] ||
     [[ "$subject_lower" =~ ^(add|added|adds|create|created|implement|implemented|introduce|introduced|new)[[:space:]:-] ]]; then
    printf '%s\n' "Added"
    return
  fi

  if [[ "$subject_lower" =~ ^(fix|bugfix|hotfix)(\(.+\))?(!)?: ]] ||
     [[ "$subject_lower" =~ ^(fix|fixed|resolve|resolved|repair|repaired|patch|patched)[[:space:]:-] ]]; then
    printf '%s\n' "Fixed"
    return
  fi

  if [[ "$subject_lower" =~ ^(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)(\(.+\))?(!)?:? ]] ||
     [[ "$subject_lower" =~ ^(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)[[:space:]:-] ]]; then
    printf '%s\n' "Removed"
    return
  fi

  if [[ "$subject_lower" =~ ^(change|changed|update|updated|refactor|perf|style|docs|test|build|ci|chore|deps|improve|improved|tweak|tweaked|rework|reworked|revert)(\(.+\))?(!)?:? ]] ||
     [[ "$subject_lower" =~ ^(change|changed|update|updated|refactor|improve|improved|tweak|tweaked|rework|reworked)[[:space:]:-] ]]; then
    printf '%s\n' "Changed"
    return
  fi

  printf '%s\n' "Changed"
}

append_commit() {
  hash="$1"
  subject="$2"
  category="$(categorize_commit "$subject")"
  line="- $subject ($hash)"

  case "$category" in
    Added) printf '%s\n' "$line" >> "$added_file" ;;
    Fixed) printf '%s\n' "$line" >> "$fixed_file" ;;
    Changed) printf '%s\n' "$line" >> "$changed_file" ;;
    Removed) printf '%s\n' "$line" >> "$removed_file" ;;
    *) printf '%s\n' "$line" >> "$changed_file" ;;
  esac
}

if [ -n "$range" ]; then
  commit_count="$(git rev-list --count $merge_arg "$range")"
else
  commit_count="$(git rev-list --count $merge_arg HEAD)"
fi

if [ "$commit_count" -gt 0 ]; then
  if [ -n "$range" ]; then
    git log $merge_arg --reverse --pretty=format:'%h%x09%s' "$range"
  else
    git log $merge_arg --reverse --pretty=format:'%h%x09%s' HEAD
  fi | while IFS="$(printf '\t')" read -r hash subject || [ -n "$hash" ]; do
    [ -n "$hash" ] || continue
    append_commit "$hash" "$subject"
  done
fi

render_section() {
  title="$1"
  file="$2"

  if [ -s "$file" ]; then
    printf '### %s\n\n' "$title"
    cat "$file"
    printf '\n\n'
  fi
}

new_changelog="$tmp_dir/CHANGELOG.md"
today="$(date +%Y-%m-%d)"

{
  printf '# Changelog\n\n'
  printf '## [Unreleased] - %s\n\n' "$today"
  printf '%s\n\n' "$range_note"

  if [ "$commit_count" -eq 0 ]; then
    printf 'No changes found.\n\n'
  else
    render_section "Added" "$added_file"
    render_section "Fixed" "$fixed_file"
    render_section "Changed" "$changed_file"
    render_section "Removed" "$removed_file"
  fi

  if [ -f "$output_path" ]; then
    existing_body="$tmp_dir/existing-body.md"
    sed '1{/^# Changelog$/d;}' "$output_path" > "$existing_body"
    if [ -s "$existing_body" ]; then
      cat "$existing_body"
    fi
  fi
} > "$new_changelog"

mv "$new_changelog" "$output_path"

printf 'Wrote %s from %s commit(s).\n' "$output_path" "$commit_count"
