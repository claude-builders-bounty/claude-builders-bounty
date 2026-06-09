#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "generate-changelog: run this inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  since_label="since ${latest_tag}"
else
  range="HEAD"
  since_label="for all commits"
fi

commit_lines="$(git log --no-merges --pretty=format:'%s' "$range" 2>/dev/null || true)"
if [[ -z "$commit_lines" ]]; then
  {
    echo "# Changelog"
    echo
    echo "No changes found ${since_label}."
  } > "$OUTPUT_FILE"
  echo "Wrote $OUTPUT_FILE"
  exit 0
fi

categorize_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feature:*|add:*|added:*|add' '*|added' '*|*' add '*|*' adds '*|*' introduce '*|*' introduces '*)
      printf 'Added'
      ;;
    fix:*|bugfix:*|hotfix:*|fix' '*|fixed' '*|*' fix '*|*' fixes '*|*' fixed '*|*' bug '*)
      printf 'Fixed'
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*|remove' '*|removed' '*|delete' '*|deleted' '*|drop' '*|dropped' '*|*' remove '*|*' removes '*|*' delete '*|*' deletes '*)
      printf 'Removed'
      ;;
    refactor:*|change:*|changed:*|update:*|updated:*|docs:*|doc:*|style:*|test:*|chore:*|perf:*)
      printf 'Changed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

for category in Added Fixed Changed Removed; do
  : > "${tmp_dir}/${category}"
done

while IFS= read -r subject; do
  [[ -z "$subject" ]] && continue
  category="$(categorize_commit "$subject")"
  printf -- '- %s\n' "$subject" >> "${tmp_dir}/${category}"
done <<< "$commit_lines"

{
  echo "# Changelog"
  echo
  echo "Generated from git history ${since_label}."
  echo
  for category in Added Fixed Changed Removed; do
    if [[ -s "${tmp_dir}/${category}" ]]; then
      echo "## ${category}"
      echo
      cat "${tmp_dir}/${category}"
      echo
    fi
  done
} > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE"
