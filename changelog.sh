#!/usr/bin/env bash
set -euo pipefail

output_file="${1:-CHANGELOG.md}"
version="${CHANGELOG_VERSION:-Unreleased}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: changelog.sh must be run inside a git repository." >&2
  exit 1
fi

last_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
range=()
scope_text="full git history"

if [ -n "$last_tag" ]; then
  range=("${last_tag}..HEAD")
  scope_text="commits since ${last_tag}"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

added_file="${tmp_dir}/added"
fixed_file="${tmp_dir}/fixed"
changed_file="${tmp_dir}/changed"
removed_file="${tmp_dir}/removed"
: >"$added_file"
: >"$fixed_file"
: >"$changed_file"
: >"$removed_file"

categorize_commit() {
  subject="$1"
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feat\(*|feature:*|feature\(*|add:*|add\(*|added:*|added\(*)
      printf '%s\n' "$added_file"
      ;;
    fix:*|fix\(*|bugfix:*|bugfix\(*|hotfix:*|hotfix\(*)
      printf '%s\n' "$fixed_file"
      ;;
    remove:*|remove\(*|removed:*|removed\(*|delete:*|delete\(*|deleted:*|deleted\(*|drop:*|drop\(*)
      printf '%s\n' "$removed_file"
      ;;
    *)
      if printf '%s' "$normalized" | grep -Eq '(^|[[:space:]])(add|adds|added|introduce|introduces|introduced)([[:space:]]|$)'; then
        printf '%s\n' "$added_file"
      elif printf '%s' "$normalized" | grep -Eq '(^|[[:space:]])(fix|fixes|fixed|bug|bugs|repair|repairs|repaired)([[:space:]]|$)'; then
        printf '%s\n' "$fixed_file"
      elif printf '%s' "$normalized" | grep -Eq '(^|[[:space:]])(remove|removes|removed|delete|deletes|deleted|drop|drops|dropped)([[:space:]]|$)'; then
        printf '%s\n' "$removed_file"
      else
        printf '%s\n' "$changed_file"
      fi
      ;;
  esac
}

commit_count=0
while IFS=$'\t' read -r subject short_sha; do
  [ -n "$subject" ] || continue
  category_file="$(categorize_commit "$subject")"
  printf -- '- %s (`%s`)\n' "$subject" "$short_sha" >>"$category_file"
  commit_count=$((commit_count + 1))
done < <(git log --reverse --no-merges --format='%s%x09%h' "${range[@]}")

write_section() {
  title="$1"
  file="$2"

  printf '\n### %s\n' "$title"
  if [ -s "$file" ]; then
    cat "$file"
  else
    printf -- '- No changes.\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf '## %s\n\n' "$version"
  printf '_Generated from %s on %s._\n' "$scope_text" "$(date -u '+%Y-%m-%d')"

  if [ "$commit_count" -eq 0 ]; then
    printf '\nNo commits found for this range.\n'
  else
    write_section "Added" "$added_file"
    write_section "Fixed" "$fixed_file"
    write_section "Changed" "$changed_file"
    write_section "Removed" "$removed_file"
  fi
} >"$output_file"

echo "Wrote $output_file from $commit_count commit(s)."
