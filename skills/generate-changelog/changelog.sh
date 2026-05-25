#!/usr/bin/env bash
set -euo pipefail

output="CHANGELOG.md"

usage() {
  cat <<'USAGE'
Usage: bash changelog.sh [-o CHANGELOG.md]

Generate a structured CHANGELOG.md from commits since the latest git tag.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      output="${2:-}"
      if [[ -z "$output" ]]; then
        echo "Missing value for $1" >&2
        exit 2
      fi
      shift 2
      ;;
    -h|--help)
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

git rev-parse --is-inside-work-tree >/dev/null

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$latest_tag" ]]; then
  range="${latest_tag}..HEAD"
  since_text="since ${latest_tag}"
else
  range="HEAD"
  since_text="for all commits because no git tag was found"
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

added="$tmpdir/added"
fixed="$tmpdir/fixed"
changed="$tmpdir/changed"
removed="$tmpdir/removed"
touch "$added" "$fixed" "$changed" "$removed"

classify_commit() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|add:*|add\ *|added:*|new:*)
      printf '%s\n' "$added"
      ;;
    fix:*|fix\(*|fixed:*|bug:*|bugfix:*|hotfix:*)
      printf '%s\n' "$fixed"
      ;;
    remove:*|remove\ *|removed:*|delete:*|delete\ *|drop:*|drop\ *|deprecate:*)
      printf '%s\n' "$removed"
      ;;
    *)
      printf '%s\n' "$changed"
      ;;
  esac
}

append_commit() {
  local bucket="$1"
  local hash="$2"
  local subject="$3"
  local author="$4"
  local date="$5"

  printf -- '- %s (`%s`, %s, %s)\n' "$subject" "${hash:0:7}" "$author" "$date" >> "$bucket"
}

while IFS=$'\x1f' read -r hash subject author date; do
  [[ -n "${hash:-}" ]] || continue
  bucket="$(classify_commit "$subject")"
  append_commit "$bucket" "$hash" "$subject" "$author" "$date"
done < <(git log "$range" --no-merges --date=short --format=$'%H%x1f%s%x1f%an%x1f%ad')

write_section() {
  local title="$1"
  local file="$2"

  printf '## %s\n\n' "$title"
  if [[ -s "$file" ]]; then
    cat "$file"
  else
    printf -- '- No entries.\n'
  fi
  printf '\n'
}

{
  printf '# Changelog\n\n'
  printf 'Generated on %s from git history %s.\n\n' "$(date -u +%Y-%m-%d)" "$since_text"
  write_section "Added" "$added"
  write_section "Fixed" "$fixed"
  write_section "Changed" "$changed"
  write_section "Removed" "$removed"
} > "$output"

echo "Wrote $output"
