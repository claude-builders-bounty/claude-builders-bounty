#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run from inside a git repository" >&2
  exit 1
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
today="$(date +%Y-%m-%d)"
latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -n "$latest_tag" ]]; then
  commit_range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  commit_range="HEAD"
  range_label="from the full repository history"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added_file="$tmp_dir/added.md"
fixed_file="$tmp_dir/fixed.md"
changed_file="$tmp_dir/changed.md"
removed_file="$tmp_dir/removed.md"
other_file="$tmp_dir/other.md"
: >"$added_file"
: >"$fixed_file"
: >"$changed_file"
: >"$removed_file"
: >"$other_file"

categorize_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feature:*|add:*|added:*|add\ *|adds\ *|added\ *|*' add '*|*' adds '*|*' added '*)
      printf '%s' "$added_file"
      ;;
    fix:*|bugfix:*|hotfix:*|fix\ *|fixes\ *|fixed\ *|*' fix '*|*' fixes '*|*' fixed '*|*' bug '*)
      printf '%s' "$fixed_file"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|remove\ *|removes\ *|removed\ *|delete\ *|deletes\ *|deleted\ *|*' remove '*|*' removed '*|*' delete '*|*' deleted '*)
      printf '%s' "$removed_file"
      ;;
    refactor:*|change:*|changed:*|update:*|updated:*|docs:*|chore:*|style:*|test:*|change\ *|changes\ *|changed\ *|update\ *|updates\ *|updated\ *|*' change '*|*' changed '*|*' update '*|*' updated '*)
      printf '%s' "$changed_file"
      ;;
    *)
      printf '%s' "$other_file"
      ;;
  esac
}

while IFS=$'\t' read -r short_hash subject || [[ -n "${short_hash:-}" ]]; do
  [[ -z "${short_hash:-}" ]] && continue
  target_file="$(categorize_commit "$subject")"
  printf -- '- %s ([%s](../../commit/%s))\n' "$subject" "$short_hash" "$short_hash" >>"$target_file"
done < <(git log "$commit_range" --no-merges --date-order --pretty=format:'%h%x09%s')

{
  printf '# Changelog\n\n'
  printf 'All notable changes for `%s` are listed here.\n\n' "$repo_name"
  printf '## %s\n\n' "$today"
  printf '_Generated from commits %s._\n\n' "$range_label"

  for section in Added Fixed Changed Removed; do
    case "$section" in
      Added) file="$added_file"; empty_label="added entries" ;;
      Fixed) file="$fixed_file"; empty_label="fixes" ;;
      Changed) file="$changed_file"; empty_label="changes" ;;
      Removed) file="$removed_file"; empty_label="removals" ;;
    esac

    printf '### %s\n\n' "$section"
    if [[ -s "$file" ]]; then
      cat "$file"
    else
      printf -- '- No %s detected.\n' "$empty_label"
    fi
    printf '\n'
  done

  if [[ -s "$other_file" ]]; then
    printf '### Other\n\n'
    cat "$other_file"
    printf '\n'
  fi
} >"$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE"
