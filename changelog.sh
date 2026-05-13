#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$(dirname "$0")/generate_changelog.py" "$OUTPUT_FILE"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$(dirname "$0")/generate_changelog.py" "$OUTPUT_FILE"
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: changelog.sh must be run inside a git repository" >&2
  exit 1
fi

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [ -n "$latest_tag" ]; then
  range="${latest_tag}..HEAD"
  range_label="since ${latest_tag}"
else
  range="HEAD"
  range_label="from repository history"
fi

repo_name="$(basename "$(git rev-parse --show-toplevel)")"
today="$(date +%Y-%m-%d)"

commit_lines="$(git log "$range" --no-merges --pretty=format:'%s%x09%h' 2>/dev/null || true)"

if [ -z "$commit_lines" ]; then
  {
    echo "# Changelog"
    echo
    echo "## ${today}"
    echo
    echo "_No commits found ${range_label}._"
  } > "$OUTPUT_FILE"
  echo "Wrote ${OUTPUT_FILE}"
  exit 0
fi

added_file="$(mktemp)"
fixed_file="$(mktemp)"
changed_file="$(mktemp)"
removed_file="$(mktemp)"
trap 'rm -f "$added_file" "$fixed_file" "$changed_file" "$removed_file"' EXIT

append_commit() {
  local subject="$1"
  local hash="$2"
  local bucket="$changed_file"
  local normalized
  normalized="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$normalized" in
    feat:*|feature:*|add:*|added:*|*' add '*|*' adds '*|*' introduce '*|*' introduces '*')
      bucket="$added_file"
      ;;
    fix:*|bugfix:*|hotfix:*|*' fix '*|*' fixes '*|*' bug '*|*' repair '*')
      bucket="$fixed_file"
      ;;
    remove:*|removed:*|delete:*|deleted:*|drop:*|*' remove '*|*' removes '*|*' delete '*|*' deletes '*')
      bucket="$removed_file"
      ;;
    refactor:*|change:*|changed:*|update:*|updated:*|perf:*|docs:*|style:*|test:*|chore:*)
      bucket="$changed_file"
      ;;
  esac

  printf -- '- %s (`%s`)\n' "$subject" "$hash" >> "$bucket"
}

while IFS=$'\t' read -r subject hash; do
  [ -n "$subject" ] || continue
  append_commit "$subject" "$hash"
done <<EOF
$commit_lines
EOF

write_section() {
  local title="$1"
  local file="$2"
  echo "### ${title}"
  echo
  if [ -s "$file" ]; then
    cat "$file"
  else
    echo "_No entries._"
  fi
  echo
}

{
  echo "# Changelog"
  echo
  echo "## ${today}"
  echo
  echo "Generated for \`${repo_name}\` ${range_label}."
  echo
  write_section "Added" "$added_file"
  write_section "Fixed" "$fixed_file"
  write_section "Changed" "$changed_file"
  write_section "Removed" "$removed_file"
} > "$OUTPUT_FILE"

echo "Wrote ${OUTPUT_FILE}"
