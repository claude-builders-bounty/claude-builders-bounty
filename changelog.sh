#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh must be run inside a git repository." >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  source_label="Changes since ${latest_tag}"
else
  range="HEAD"
  source_label="Changes from all commits"
fi

today="$(date +%Y-%m-%d)"
repo_root="$(git rev-parse --show-toplevel)"
output_file="${repo_root}/CHANGELOG.md"

added_file="$(mktemp)"
fixed_file="$(mktemp)"
changed_file="$(mktemp)"
removed_file="$(mktemp)"
trap 'rm -f "$added_file" "$fixed_file" "$changed_file" "$removed_file"' EXIT

append_commit() {
  local subject="$1"
  local hash="$2"
  local target="$3"

  printf -- "- %s (%s)\n" "$subject" "$hash" >> "$target"
}

categorize_commit() {
  local subject="$1"
  local normalized

  normalized="$(printf "%s" "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feat'('*'):'*|feature:*|feature'('*'):'*|add:*|added:*|new:*|create:*|implement:*)
      printf "added"
      ;;
    fix:*|fix'('*'):'*|fixed:*|bugfix:*|resolve:*|resolved:*|repair:*)
      printf "fixed"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|deprecate:*|deprecated:*)
      printf "removed"
      ;;
    *)
      printf "changed"
      ;;
  esac
}

commit_count=0
while IFS=$'\t' read -r hash subject; do
  [[ -n "${hash:-}" ]] || continue
  commit_count=$((commit_count + 1))
  short_hash="${hash:0:7}"
  category="$(categorize_commit "$subject")"

  case "$category" in
    added) append_commit "$subject" "$short_hash" "$added_file" ;;
    fixed) append_commit "$subject" "$short_hash" "$fixed_file" ;;
    removed) append_commit "$subject" "$short_hash" "$removed_file" ;;
    *) append_commit "$subject" "$short_hash" "$changed_file" ;;
  esac
done < <(git log --reverse --format=$'%H\t%s' "$range")

{
  printf "# Changelog\n\n"
  printf "## Unreleased - %s\n\n" "$today"
  printf "_%s_\n\n" "$source_label"

  if [[ "$commit_count" -eq 0 ]]; then
    printf "No changes since the last git tag.\n"
  else
    for section in Added Fixed Changed Removed; do
      case "$section" in
        Added) section_file="$added_file" ;;
        Fixed) section_file="$fixed_file" ;;
        Changed) section_file="$changed_file" ;;
        Removed) section_file="$removed_file" ;;
      esac

      printf "### %s\n\n" "$section"
      if [[ -s "$section_file" ]]; then
        cat "$section_file"
      else
        printf -- "- No %s changes.\n" "$(printf "%s" "$section" | tr '[:upper:]' '[:lower:]')"
      fi
      printf "\n"
    done
  fi
} > "$output_file"

echo "Wrote ${output_file}"
