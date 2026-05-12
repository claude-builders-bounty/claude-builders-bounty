#!/usr/bin/env bash
set -euo pipefail

output="${1:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "generate-changelog: run inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  heading="Unreleased changes since ${latest_tag}"
else
  range="HEAD"
  heading="Unreleased changes"
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

while IFS=$'\t' read -r hash subject || [[ -n "${hash:-}" ]]; do
  [[ -z "${hash:-}" ]] && continue
  line="- ${subject} (${hash})"
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    feat:*|feature:*|add:*|added:*) echo "$line" >>"$added" ;;
    fix:*|bugfix:*|fixed:*) echo "$line" >>"$fixed" ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|dropped:*) echo "$line" >>"$removed" ;;
    *) echo "$line" >>"$changed" ;;
  esac
done < <(git log --no-merges --pretty=format:'%h%x09%s' "$range")

{
  echo "# Changelog"
  echo
  echo "## ${heading}"
  echo
  for section in Added Fixed Changed Removed; do
    file="$tmp_dir/$(printf '%s' "$section" | tr '[:upper:]' '[:lower:]')"
    if [[ -s "$file" ]]; then
      echo "### ${section}"
      cat "$file"
      echo
    fi
  done
} >"$output"

echo "Wrote ${output}"
