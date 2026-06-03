#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-.}"
OUTPUT_FILE="${2:-$REPO_DIR/CHANGELOG.md}"

if ! git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: $REPO_DIR is not a git repository." >&2
  exit 1
fi

latest_tag="$(git -C "$REPO_DIR" describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="$latest_tag..HEAD"
  range_label="Changes since $latest_tag"
else
  range="HEAD"
  range_label="All commits"
fi

commit_count="$(git -C "$REPO_DIR" rev-list --count "$range" 2>/dev/null || echo "0")"
generated_at="$(date -u +"%Y-%m-%d")"

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

added="$tmp_dir/added"
fixed="$tmp_dir/fixed"
changed="$tmp_dir/changed"
removed="$tmp_dir/removed"
: > "$added"
: > "$fixed"
: > "$changed"
: > "$removed"

normalize_subject() {
  local subject="$1"

  subject="${subject#feat: }"
  subject="${subject#feat!: }"
  subject="${subject#feature: }"
  subject="${subject#add: }"
  subject="${subject#fix: }"
  subject="${subject#bugfix: }"
  subject="${subject#docs: }"
  subject="${subject#doc: }"
  subject="${subject#refactor: }"
  subject="${subject#change: }"
  subject="${subject#chore: }"
  subject="${subject#remove: }"
  subject="${subject#removed: }"
  subject="${subject#delete: }"
  subject="${subject#deleted: }"

  printf '%s' "$subject"
}

categorize_subject() {
  local subject_lc="$1"

  case "$subject_lc" in
    feat:*|feat!:*|feature:*|add:*|added\ *|add\ *)
      printf '%s' "$added"
      ;;
    fix:*|bugfix:*|fixed\ *|fix\ *|repair\ *|resolve\ *)
      printf '%s' "$fixed"
      ;;
    remove:*|removed:*|delete:*|deleted:*|remove\ *|drop\ *|deprecate\ *)
      printf '%s' "$removed"
      ;;
    *)
      printf '%s' "$changed"
      ;;
  esac
}

if [[ "$commit_count" != "0" ]]; then
  while IFS=$'\t' read -r short_hash subject || [[ -n "${short_hash:-}" ]]; do
    [[ -z "${short_hash:-}" ]] && continue

    subject_lc="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
    category_file="$(categorize_subject "$subject_lc")"
    clean_subject="$(normalize_subject "$subject")"

    printf -- '- %s (%s)\n' "$clean_subject" "$short_hash" >> "$category_file"
  done < <(git -C "$REPO_DIR" log "$range" --reverse --pretty=format:'%h%x09%s')
fi

write_section() {
  local title="$1"
  local file="$2"

  if [[ -s "$file" ]]; then
    printf '### %s\n\n' "$title"
    cat "$file"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf '## Unreleased\n\n'
  printf '_Generated on %s from %s._\n\n' "$generated_at" "$range_label"

  if [[ "$commit_count" == "0" ]]; then
    printf 'No commits found for this range.\n'
  else
    write_section "Added" "$added"
    write_section "Fixed" "$fixed"
    write_section "Changed" "$changed"
    write_section "Removed" "$removed"
  fi
} > "$OUTPUT_FILE"

echo "Wrote $OUTPUT_FILE"
