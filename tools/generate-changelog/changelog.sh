#!/usr/bin/env bash

set -euo pipefail

output_path="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
range=()
range_label="all history"

if [[ -n "$latest_tag" ]]; then
  range=("${latest_tag}..HEAD")
  range_label="since ${latest_tag}"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added_file="$tmp_dir/added"
fixed_file="$tmp_dir/fixed"
changed_file="$tmp_dir/changed"
removed_file="$tmp_dir/removed"
: >"$added_file"
: >"$fixed_file"
: >"$changed_file"
: >"$removed_file"

clean_subject() {
  local subject="$1"
  subject="$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  subject="$(printf '%s' "$subject" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')"
  if [[ -z "$subject" ]]; then
    subject="Untitled commit"
  fi
  printf '%s' "$subject"
}

append_entry() {
  local file="$1"
  local subject="$2"
  local sha="$3"
  local date="$4"

  printf -- '- %s (`%s`, %s)\n' "$(clean_subject "$subject")" "${sha:0:7}" "$date" >>"$file"
}

while IFS=$'\t' read -r sha date subject; do
  [[ -n "${sha:-}" ]] || continue

  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feat\(*|feature:*|feature\(*|add:*|add\(*|added:*|added\(*|create:*|create\(*|implement:*|implement\(*|introduce:*|introduce\(*|initial*)
      append_entry "$added_file" "$subject" "$sha" "$date"
      ;;
    fix:*|fix\(*|bugfix:*|bugfix\(*|bug:*|bug\(*|patch:*|patch\(*|resolve:*|resolve\(*|repair:*|repair\(*|correct:*|correct\(*)
      append_entry "$fixed_file" "$subject" "$sha" "$date"
      ;;
    remove:*|remove\(*|removed:*|removed\(*|delete:*|delete\(*|drop:*|drop\(*|deprecate:*|deprecate\(*)
      append_entry "$removed_file" "$subject" "$sha" "$date"
      ;;
    docs:*|docs\(*|doc:*|doc\(*|chore:*|chore\(*|refactor:*|refactor\(*|style:*|style\(*|perf:*|perf\(*|test:*|test\(*|ci:*|ci\(*|build:*|build\(*|update:*|update\(*|improve:*|improve\(*|change:*|change\(*)
      append_entry "$changed_file" "$subject" "$sha" "$date"
      ;;
    *)
      append_entry "$changed_file" "$subject" "$sha" "$date"
      ;;
  esac
done < <(git log "${range[@]}" --reverse --date=short --format='%H%x09%ad%x09%s')

commit_count="$(git log "${range[@]}" --format='%H' | wc -l | tr -d '[:space:]')"
generated_at="$(date -u '+%Y-%m-%d')"

{
  printf '# Changelog\n\n'
  printf 'Generated from git history on %s. Commit range: %s.\n\n' "$generated_at" "$range_label"
  printf '## Unreleased\n\n'

  if [[ "$commit_count" == "0" ]]; then
    printf 'No commits found for this range.\n'
  else
    for section in Added Fixed Changed Removed; do
      case "$section" in
        Added) file="$added_file" ;;
        Fixed) file="$fixed_file" ;;
        Changed) file="$changed_file" ;;
        Removed) file="$removed_file" ;;
      esac

      if [[ -s "$file" ]]; then
        printf '### %s\n\n' "$section"
        cat "$file"
        printf '\n'
      fi
    done
  fi
} >"$output_path"

echo "Wrote ${output_path} from ${commit_count} commit(s) (${range_label})."
